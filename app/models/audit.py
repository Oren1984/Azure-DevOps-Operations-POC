"""AuditRecord domain model. Every meaningful action is recorded here."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.enums import AuditAction


class AuditRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str
    entity_type: str
    entity_id: str
    action: AuditAction
    actor: str
    result: str
    metadata: dict[str, Any] = Field(default_factory=dict)
