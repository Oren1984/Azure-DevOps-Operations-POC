"""Deterministic, offline demo scenario.

Walks the system through a full incident lifecycle: a healthy baseline, a
failed deployment, compounding warning signals that escalate the incident
to CRITICAL, a human approval decision, a simulated rollback, and recovery.
Every step uses the same correlation ID so the resulting audit trail reads
as one coherent story. No Azure credentials or network access are used.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.correlation import new_correlation_id
from app.models.audit import AuditRecord
from app.models.enums import AuditAction, EventType
from app.models.events import EventPayload, OperationalEventCreate
from app.services.audit_service import AuditService
from app.services.event_service import EventOutcome, EventService
from app.services.incident_service import IncidentService

DEMO_SOURCE = "checkout-service"


@dataclass
class DemoStepResult:
    name: str
    outcome: EventOutcome


@dataclass
class DemoResult:
    correlation_id: str
    steps: list[DemoStepResult] = field(default_factory=list)
    audit_trail: list[AuditRecord] = field(default_factory=list)


class DemoService:
    def __init__(
        self,
        event_service: EventService,
        incident_service: IncidentService,
        audit_service: AuditService,
    ) -> None:
        self._events = event_service
        self._incidents = incident_service
        self._audit = audit_service

    def run(self) -> DemoResult:
        correlation_id = new_correlation_id()
        result = DemoResult(correlation_id=correlation_id)

        def submit(name: str, event_type: EventType, payload: EventPayload) -> EventOutcome:
            outcome = self._events.submit_event(
                OperationalEventCreate(event_type=event_type, source=DEMO_SOURCE, payload=payload),
                correlation_id=correlation_id,
            )
            result.steps.append(DemoStepResult(name=name, outcome=outcome))
            return outcome

        # 1. Healthy baseline.
        submit("healthy_baseline", EventType.DEPLOYMENT_SUCCEEDED, EventPayload())

        # 2. A deployment fails.
        submit("deployment_failed", EventType.DEPLOYMENT_FAILED, EventPayload())

        # 3. Readiness probe starts failing (recorded, but on its own stays below
        #    the HIGH threshold so it does not yet escalate the incident).
        submit("readiness_probe_failure", EventType.READINESS_PROBE_FAILURE, EventPayload())

        # 4. Pod restarts, elevated error rate, and elevated latency all arrive
        #    together, compounding into a CRITICAL incident that recommends rollback.
        incident_outcome = submit(
            "compounding_warning_signals",
            EventType.POD_RESTART_THRESHOLD_EXCEEDED,
            EventPayload(restart_count=6, error_rate=0.09, latency_ms=1200),
        )
        assert incident_outcome.incident is not None

        # 7. A human approves the recommended rollback.
        approved_incident = self._incidents.approve(
            incident_outcome.incident.id,
            actor="demo-operator",
            reason="Rollback approved based on compounded risk signals.",
            correlation_id=correlation_id,
        )

        # 8. Rollback completes.
        submit("rollback_completed", EventType.ROLLBACK_COMPLETED, EventPayload())

        # 9. Application confirms recovery.
        submit("application_recovered", EventType.APPLICATION_RECOVERED, EventPayload())

        self._audit.record(
            correlation_id=correlation_id,
            entity_type="demo",
            entity_id=correlation_id,
            action=AuditAction.DEMO_SCENARIO_COMPLETED,
            actor="demo",
            result="completed",
            metadata={
                "source": DEMO_SOURCE,
                "final_incident_status": approved_incident.approval_status.value,
            },
        )

        result.audit_trail = self._audit.history(correlation_id=correlation_id)
        return result
