"""RiskAssessment domain model produced by the deterministic rule engine."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from app.models.enums import RecommendedAction, Severity


class TriggeredRule(BaseModel):
    """A single rule that fired during assessment, with its contribution."""

    rule_id: str
    description: str
    score_delta: int


class RiskAssessment(BaseModel):
    """The explainable output of evaluating one OperationalEvent."""

    event_id: str
    risk_score: int = Field(ge=0, le=100)
    severity: Severity
    triggered_rules: list[TriggeredRule]
    explanation: str
    recommended_action: RecommendedAction
    requires_approval: bool
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
