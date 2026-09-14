"""OperationalEvent domain model and its API-facing request shape."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.enums import EventType


class EventPayload(BaseModel):
    """Optional numeric/contextual signals a source system can attach to an event.

    Every field is optional because different event types carry different
    signals (a latency event carries ``latency_ms``, a restart event carries
    ``restart_count``, etc). The rule engine only reads the fields relevant
    to the event type it is evaluating.
    """

    error_rate: float | None = Field(default=None, ge=0, le=1)
    latency_ms: float | None = Field(default=None, ge=0)
    restart_count: int | None = Field(default=None, ge=0)
    node_count_ready: int | None = Field(default=None, ge=0)
    node_count_total: int | None = Field(default=None, ge=0)
    message: str | None = None

    model_config = {"extra": "allow"}


class OperationalEventCreate(BaseModel):
    """Inbound request body for POST /api/v1/events."""

    event_type: EventType
    source: str = Field(min_length=1, max_length=200, description="Service, pod, or node name")
    payload: EventPayload = Field(default_factory=EventPayload)
    occurred_at: datetime | None = None


class OperationalEvent(BaseModel):
    """A validated, persisted operational event."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType
    source: str
    payload: EventPayload = Field(default_factory=EventPayload)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    received_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str

    def payload_dict(self) -> dict[str, Any]:
        return self.payload.model_dump(exclude_none=True)
