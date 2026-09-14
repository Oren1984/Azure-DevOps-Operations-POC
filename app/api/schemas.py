"""API request/response envelopes. Kept separate from domain models so the
wire format can evolve independently of the internal representation."""

from __future__ import annotations

from pydantic import BaseModel

from app.models.assessment import RiskAssessment
from app.models.events import OperationalEvent
from app.models.incident import IncidentRecord


class EventSubmissionResponse(BaseModel):
    event: OperationalEvent
    assessment: RiskAssessment
    incident_id: str | None


class ApprovalDecisionRequest(BaseModel):
    actor: str
    reason: str | None = None


class ErrorResponse(BaseModel):
    detail: str


class DemoStepView(BaseModel):
    name: str
    event: OperationalEvent
    assessment: RiskAssessment
    incident_id: str | None


class DemoRunResponse(BaseModel):
    correlation_id: str
    steps: list[DemoStepView]
    final_incident: IncidentRecord | None
    audit_trail_count: int
