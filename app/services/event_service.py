"""Orchestrates the full event -> assessment -> incident -> audit flow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.config import Settings
from app.core.errors import NotFoundError
from app.domain import rule_engine
from app.integrations.ai_assistant import FallbackIncidentAssistant, IncidentAssistant
from app.models.assessment import RiskAssessment
from app.models.enums import ApprovalStatus, AuditAction, EventType
from app.models.events import OperationalEvent, OperationalEventCreate
from app.models.incident import IncidentRecord
from app.monitoring.metrics import Metrics
from app.repositories.base import EventRepository, IncidentRepository
from app.services.audit_service import AuditService

RECOVERY_EVENT_TYPES = frozenset({EventType.APPLICATION_RECOVERED, EventType.ROLLBACK_COMPLETED})


@dataclass
class EventOutcome:
    event: OperationalEvent
    assessment: RiskAssessment
    incident: IncidentRecord | None


class EventService:
    def __init__(
        self,
        settings: Settings,
        event_repository: EventRepository,
        incident_repository: IncidentRepository,
        audit_service: AuditService,
        incident_assistant: IncidentAssistant,
        metrics: Metrics,
    ) -> None:
        self._settings = settings
        self._events = event_repository
        self._incidents = incident_repository
        self._audit = audit_service
        self._assistant = incident_assistant
        self._metrics = metrics

    def submit_event(self, request: OperationalEventCreate, correlation_id: str) -> EventOutcome:
        event_kwargs = dict(
            event_type=request.event_type,
            source=request.source,
            payload=request.payload,
            correlation_id=correlation_id,
        )
        if request.occurred_at is not None:
            event_kwargs["occurred_at"] = request.occurred_at
        event = OperationalEvent(**event_kwargs)
        self._events.save(event)
        self._metrics.events_received_total.labels(event_type=event.event_type.value).inc()
        self._audit.record(
            correlation_id=correlation_id,
            entity_type="event",
            entity_id=event.id,
            action=AuditAction.EVENT_RECEIVED,
            actor="api",
            result="stored",
            metadata={"event_type": event.event_type.value, "source": event.source},
        )

        assessment = rule_engine.assess(event, self._settings)
        self._metrics.assessments_total.labels(severity=assessment.severity.value).inc()
        self._audit.record(
            correlation_id=correlation_id,
            entity_type="event",
            entity_id=event.id,
            action=AuditAction.ASSESSMENT_GENERATED,
            actor="rule_engine",
            result=assessment.severity.value,
            metadata={
                "risk_score": assessment.risk_score,
                "action": assessment.recommended_action.value,
            },
        )

        incident = self._apply_incident_lifecycle(event, assessment, correlation_id)
        return EventOutcome(event=event, assessment=assessment, incident=incident)

    def _apply_incident_lifecycle(
        self, event: OperationalEvent, assessment: RiskAssessment, correlation_id: str
    ) -> IncidentRecord | None:
        active = self._incidents.find_active_by_source(event.source)

        if event.event_type in RECOVERY_EVENT_TYPES and active is not None:
            active.resolved = True
            active.resolved_at = datetime.now(UTC)
            active.updated_at = active.resolved_at
            self._incidents.save(active)
            self._audit.record(
                correlation_id=correlation_id,
                entity_type="incident",
                entity_id=active.id,
                action=AuditAction.INCIDENT_RESOLVED,
                actor="rule_engine",
                result="resolved",
                metadata={"triggering_event_id": event.id, "event_type": event.event_type.value},
            )
            return active

        if assessment.severity.value in ("high", "critical"):
            if active is not None:
                incident = active
                incident.event_id = event.id
                incident.assessment = assessment
                incident.updated_at = datetime.now(UTC)
                if (
                    assessment.requires_approval
                    and incident.approval_status == ApprovalStatus.NOT_REQUIRED
                ):
                    # The incident escalated after it was opened: a decision is now needed.
                    incident.approval_status = ApprovalStatus.PENDING
            else:
                incident = IncidentRecord(
                    source=event.source,
                    event_id=event.id,
                    assessment=assessment,
                    approval_status=(
                        ApprovalStatus.PENDING
                        if assessment.requires_approval
                        else ApprovalStatus.NOT_REQUIRED
                    ),
                )

            fallback_used = False
            if isinstance(self._assistant, FallbackIncidentAssistant):
                ai_summary, fallback_used = self._assistant.summarize_with_status(
                    event.source, assessment
                )
            else:
                ai_summary = self._assistant.summarize(event.source, assessment)
            incident.ai_summary = ai_summary

            self._incidents.save(incident)
            action = (
                AuditAction.INCIDENT_OPENED if active is None else AuditAction.ASSESSMENT_GENERATED
            )
            self._audit.record(
                correlation_id=correlation_id,
                entity_type="incident",
                entity_id=incident.id,
                action=action,
                actor="rule_engine",
                result=assessment.severity.value,
                metadata={"requires_approval": assessment.requires_approval},
            )
            self._audit.record(
                correlation_id=correlation_id,
                entity_type="incident",
                entity_id=incident.id,
                action=AuditAction.AI_SUMMARY_REQUESTED,
                actor="incident_assistant",
                result=ai_summary.source,
                metadata={"is_ai_generated": ai_summary.is_ai_generated},
            )
            if fallback_used:
                self._metrics.ai_fallback_total.inc()
                self._audit.record(
                    correlation_id=correlation_id,
                    entity_type="incident",
                    entity_id=incident.id,
                    action=AuditAction.AI_FALLBACK_ACTIVATED,
                    actor="incident_assistant",
                    result="fallback_to_deterministic",
                    metadata={},
                )
            if incident.approval_status == ApprovalStatus.PENDING:
                self._audit.record(
                    correlation_id=correlation_id,
                    entity_type="incident",
                    entity_id=incident.id,
                    action=AuditAction.APPROVAL_REQUESTED,
                    actor="rule_engine",
                    result="pending",
                    metadata={"recommended_action": assessment.recommended_action.value},
                )
            return incident

        return active

    def get_event(self, event_id: str) -> OperationalEvent:
        event = self._events.get(event_id)
        if event is None:
            raise NotFoundError(f"event {event_id} not found")
        return event

    def list_events(self, limit: int = 100) -> list[OperationalEvent]:
        return self._events.list(limit=limit)
