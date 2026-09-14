"""Optional, read-only incident assistant.

This is intentionally small. It is not a core project requirement — it
exists to illustrate one safe pattern for integrating Azure OpenAI into an
operational tool: strict output validation and an automatic, silent
fallback to a deterministic implementation on any failure.

Hard rule: nothing in this module is allowed to return anything other than
a natural-language summary and a list of suggested investigation steps. It
cannot trigger a rollback, scale, delete, or configuration change, and its
output is always labeled with where it came from (``source`` /
``is_ai_generated`` on IncidentAssistantResponse).
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Protocol

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.core.logging import get_logger
from app.models.ai import IncidentAssistantResponse
from app.models.assessment import RiskAssessment

logger = get_logger(__name__)


class IncidentAssistant(ABC):
    @abstractmethod
    def summarize(self, source: str, assessment: RiskAssessment) -> IncidentAssistantResponse: ...


class DeterministicIncidentAssistant(IncidentAssistant):
    """Default, offline implementation. Builds a summary from the rule engine's own output."""

    def summarize(self, source: str, assessment: RiskAssessment) -> IncidentAssistantResponse:
        rule_ids = [r.rule_id for r in assessment.triggered_rules]
        steps = [f"Review signal behind rule '{rid}'." for rid in rule_ids] or [
            "No specific rules triggered; review recent logs for context."
        ]
        steps.append(f"Check recent deployment and change history for '{source}'.")
        summary = (
            f"{source} reached {assessment.severity.value} severity "
            f"(risk score {assessment.risk_score}). {assessment.explanation}"
        )
        return IncidentAssistantResponse(
            summary=summary,
            suggested_investigation_steps=steps[:10],
            source="deterministic",
            is_ai_generated=False,
        )


class _AzureOpenAITransport(Protocol):
    def post(self, url: str, **kwargs: object) -> httpx.Response: ...


class AzureOpenAIIncidentAssistant(IncidentAssistant):
    """Illustrative Azure OpenAI adapter.

    Calls the Azure OpenAI chat completions REST API and requires the model
    to return JSON matching IncidentAssistantResponse's fields. This is a
    minimal example, not a production client: no retries, no streaming, no
    prompt-engineering beyond a single instruction. Any failure (network,
    timeout, malformed JSON, schema mismatch) raises, and the caller
    (FallbackIncidentAssistant) is expected to fall back to the
    deterministic implementation.
    """

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        if not (
            settings.azure_openai_endpoint
            and settings.azure_openai_api_key
            and settings.azure_openai_deployment
        ):
            raise ValueError("Azure OpenAI is not fully configured")
        self._settings = settings
        self._client = client or httpx.Client(timeout=settings.azure_openai_timeout_seconds)

    def summarize(self, source: str, assessment: RiskAssessment) -> IncidentAssistantResponse:
        url = (
            f"{self._settings.azure_openai_endpoint}/openai/deployments/"
            f"{self._settings.azure_openai_deployment}/chat/completions?api-version=2024-06-01"
        )
        prompt = (
            "Summarize this operational incident in one short paragraph and list up to 5 "
            "investigation steps. Respond as JSON with keys 'summary' and 'steps' only.\n"
            f"Source: {source}\nSeverity: {assessment.severity.value}\n"
            f"Risk score: {assessment.risk_score}\nExplanation: {assessment.explanation}"
        )
        response = self._client.post(
            url,
            headers={"api-key": self._settings.azure_openai_api_key or ""},
            json={"messages": [{"role": "user", "content": prompt}], "max_tokens": 400},
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return IncidentAssistantResponse(
            summary=parsed["summary"],
            suggested_investigation_steps=parsed["steps"],
            source="azure_openai",
            is_ai_generated=True,
        )


class FallbackIncidentAssistant(IncidentAssistant):
    """Tries a primary assistant, silently falling back on any failure.

    Returns (response, fallback_activated) via `summarize_with_status` so
    callers can record an audit entry / increment a metric when the
    fallback path was used.
    """

    def __init__(self, primary: IncidentAssistant, fallback: IncidentAssistant) -> None:
        self._primary = primary
        self._fallback = fallback

    def summarize(self, source: str, assessment: RiskAssessment) -> IncidentAssistantResponse:
        response, _ = self.summarize_with_status(source, assessment)
        return response

    def summarize_with_status(
        self, source: str, assessment: RiskAssessment
    ) -> tuple[IncidentAssistantResponse, bool]:
        try:
            return self._primary.summarize(source, assessment), False
        except (
            httpx.HTTPError,
            ValidationError,
            KeyError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            logger.warning("ai_fallback_activated", extra={"reason": str(exc)})
            return self._fallback.summarize(source, assessment), True


def build_incident_assistant(settings: Settings) -> IncidentAssistant:
    """Factory: returns the deterministic assistant unless Azure OpenAI is configured."""
    if settings.ai_provider != "azure_openai":
        return DeterministicIncidentAssistant()
    try:
        primary: IncidentAssistant = AzureOpenAIIncidentAssistant(settings)
    except ValueError:
        return DeterministicIncidentAssistant()
    return FallbackIncidentAssistant(primary=primary, fallback=DeterministicIncidentAssistant())
