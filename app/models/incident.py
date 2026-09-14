"""IncidentRecord domain model.

An incident is opened whenever an assessment reaches HIGH or CRITICAL
severity for a given source, and is resolved when a recovery-type event
(APPLICATION_RECOVERED or ROLLBACK_COMPLETED) is received for that source.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.ai import IncidentAssistantResponse
from app.models.assessment import RiskAssessment
from app.models.enums import ApprovalStatus


class IncidentRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str
    event_id: str
    assessment: RiskAssessment
    approval_status: ApprovalStatus
    resolved: bool = False
    resolved_at: datetime | None = None
    decided_by: str | None = None
    decision_reason: str | None = None
    ai_summary: IncidentAssistantResponse | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
