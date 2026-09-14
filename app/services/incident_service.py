"""Human approval gate. This service only ever records a decision.

It never calls into any infrastructure, Kubernetes, or Terraform code path.
That guarantee is what makes the human-approval requirement meaningful.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.errors import ConflictError, NotFoundError
from app.models.enums import ApprovalStatus, AuditAction
from app.models.incident import IncidentRecord
from app.monitoring.metrics import Metrics
from app.repositories.base import IncidentRepository
from app.services.audit_service import AuditService


class IncidentService:
    def __init__(
        self, incident_repository: IncidentRepository, audit_service: AuditService, metrics: Metrics
    ) -> None:
        self._incidents = incident_repository
        self._audit = audit_service
        self._metrics = metrics

    def get(self, incident_id: str) -> IncidentRecord:
        incident = self._incidents.get(incident_id)
        if incident is None:
            raise NotFoundError(f"incident {incident_id} not found")
        return incident

    def list(self, limit: int = 100) -> list[IncidentRecord]:
        return self._incidents.list(limit=limit)

    def approve(
        self, incident_id: str, actor: str, reason: str | None, correlation_id: str
    ) -> IncidentRecord:
        return self._decide(incident_id, actor, reason, correlation_id, approve=True)

    def reject(
        self, incident_id: str, actor: str, reason: str | None, correlation_id: str
    ) -> IncidentRecord:
        return self._decide(incident_id, actor, reason, correlation_id, approve=False)

    def _decide(
        self,
        incident_id: str,
        actor: str,
        reason: str | None,
        correlation_id: str,
        *,
        approve: bool,
    ) -> IncidentRecord:
        incident = self.get(incident_id)
        if incident.approval_status != ApprovalStatus.PENDING:
            raise ConflictError(
                f"incident {incident_id} already has a recorded decision: "
                f"{incident.approval_status.value}"
            )

        incident.approval_status = ApprovalStatus.APPROVED if approve else ApprovalStatus.REJECTED
        incident.decided_by = actor
        incident.decision_reason = reason
        incident.updated_at = datetime.now(UTC)
        self._incidents.save(incident)
        self._metrics.approval_decisions_total.labels(decision=incident.approval_status.value).inc()

        self._audit.record(
            correlation_id=correlation_id,
            entity_type="incident",
            entity_id=incident.id,
            action=AuditAction.APPROVAL_GRANTED if approve else AuditAction.APPROVAL_REJECTED,
            actor=actor,
            result=incident.approval_status.value,
            metadata={"reason": reason} if reason else {},
        )
        return incident
