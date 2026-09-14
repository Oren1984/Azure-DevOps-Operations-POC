from __future__ import annotations

import httpx
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.integrations.ai_assistant import (
    AzureOpenAIIncidentAssistant,
    DeterministicIncidentAssistant,
    FallbackIncidentAssistant,
    build_incident_assistant,
)
from app.models.ai import IncidentAssistantResponse
from app.models.assessment import RiskAssessment
from app.models.enums import RecommendedAction, Severity


def make_assessment() -> RiskAssessment:
    return RiskAssessment(
        event_id="evt-1",
        risk_score=80,
        severity=Severity.CRITICAL,
        triggered_rules=[],
        explanation="Triggered rules: [deployment_failed] Deployment failed.",
        recommended_action=RecommendedAction.ROLLBACK,
        requires_approval=True,
    )


def test_deterministic_assistant_is_labeled_non_ai():
    assistant = DeterministicIncidentAssistant()
    response = assistant.summarize("checkout-service", make_assessment())
    assert response.source == "deterministic"
    assert response.is_ai_generated is False
    assert response.summary
    assert len(response.suggested_investigation_steps) >= 1


def test_ai_response_schema_rejects_empty_summary():
    with pytest.raises(ValidationError):
        IncidentAssistantResponse(
            summary="",
            suggested_investigation_steps=["step"],
            source="deterministic",
            is_ai_generated=False,
        )


def test_ai_response_schema_rejects_empty_steps():
    with pytest.raises(ValidationError):
        IncidentAssistantResponse(
            summary="ok",
            suggested_investigation_steps=[],
            source="deterministic",
            is_ai_generated=False,
        )


def test_azure_openai_assistant_requires_configuration():
    settings = Settings(ai_provider="azure_openai")  # no endpoint/key/deployment set
    with pytest.raises(ValueError):
        AzureOpenAIIncidentAssistant(settings)


def test_fallback_activates_on_timeout():
    class TimeoutAssistant:
        def summarize(self, source, assessment):
            raise httpx.TimeoutException("simulated timeout")

    fallback = FallbackIncidentAssistant(
        primary=TimeoutAssistant(), fallback=DeterministicIncidentAssistant()
    )
    response, used_fallback = fallback.summarize_with_status("svc", make_assessment())
    assert used_fallback is True
    assert response.source == "deterministic"


def test_fallback_activates_on_malformed_response():
    class MalformedAssistant:
        def summarize(self, source, assessment):
            raise KeyError("summary")

    fallback = FallbackIncidentAssistant(
        primary=MalformedAssistant(), fallback=DeterministicIncidentAssistant()
    )
    response, used_fallback = fallback.summarize_with_status("svc", make_assessment())
    assert used_fallback is True
    assert response.is_ai_generated is False


def test_fallback_not_used_when_primary_succeeds():
    class WorkingAssistant:
        def summarize(self, source, assessment):
            return IncidentAssistantResponse(
                summary="ok",
                suggested_investigation_steps=["step"],
                source="azure_openai",
                is_ai_generated=True,
            )

    fallback = FallbackIncidentAssistant(
        primary=WorkingAssistant(), fallback=DeterministicIncidentAssistant()
    )
    response, used_fallback = fallback.summarize_with_status("svc", make_assessment())
    assert used_fallback is False
    assert response.source == "azure_openai"


def test_factory_returns_deterministic_by_default():
    settings = Settings()
    assistant = build_incident_assistant(settings)
    assert isinstance(assistant, DeterministicIncidentAssistant)


def test_factory_falls_back_to_deterministic_when_azure_openai_unconfigured():
    settings = Settings(ai_provider="azure_openai")
    assistant = build_incident_assistant(settings)
    assert isinstance(assistant, DeterministicIncidentAssistant)
