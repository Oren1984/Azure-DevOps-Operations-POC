"""Schema for the optional, read-only incident assistant.

AI output is advisory only. It is validated against this strict schema and
is never permitted to trigger an operational action — see
app/integrations/ai_assistant.py.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class IncidentAssistantResponse(BaseModel):
    summary: str = Field(min_length=1, max_length=2000)
    suggested_investigation_steps: list[str] = Field(min_length=1, max_length=10)
    source: Literal["deterministic", "azure_openai"]
    is_ai_generated: bool
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
