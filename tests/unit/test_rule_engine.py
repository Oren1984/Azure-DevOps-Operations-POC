from __future__ import annotations

from app.core.config import Settings
from app.domain import rule_engine
from app.models.enums import EventType, RecommendedAction, Severity
from app.models.events import EventPayload, OperationalEvent


def make_event(event_type: EventType, **payload_kwargs) -> OperationalEvent:
    return OperationalEvent(
        event_type=event_type,
        source="test-service",
        payload=EventPayload(**payload_kwargs),
        correlation_id="test-correlation",
    )


def test_deployment_succeeded_is_zero_risk():
    settings = Settings()
    event = make_event(EventType.DEPLOYMENT_SUCCEEDED)
    assessment = rule_engine.assess(event, settings)
    assert assessment.risk_score == 0
    assert assessment.severity == Severity.INFO
    assert assessment.recommended_action == RecommendedAction.NONE
    assert assessment.requires_approval is False
    assert assessment.triggered_rules == []


def test_deployment_failed_triggers_rule_and_high_severity():
    settings = Settings()
    event = make_event(EventType.DEPLOYMENT_FAILED)
    assessment = rule_engine.assess(event, settings)
    assert assessment.risk_score == settings.score_deployment_failed
    assert assessment.severity == Severity.HIGH
    assert [r.rule_id for r in assessment.triggered_rules] == ["deployment_failed"]
    assert assessment.recommended_action == RecommendedAction.INVESTIGATE
    assert assessment.requires_approval is False


def test_pod_restart_threshold_triggers_by_event_type():
    settings = Settings()
    event = make_event(EventType.POD_RESTART_THRESHOLD_EXCEEDED, restart_count=5)
    assessment = rule_engine.assess(event, settings)
    assert any(r.rule_id == "pod_restart_threshold" for r in assessment.triggered_rules)


def test_pod_restart_triggers_by_numeric_threshold_regardless_of_event_type():
    settings = Settings()
    event = make_event(EventType.HIGH_ERROR_RATE, restart_count=10, error_rate=0.5)
    assessment = rule_engine.assess(event, settings)
    rule_ids = {r.rule_id for r in assessment.triggered_rules}
    assert "pod_restart_threshold" in rule_ids
    assert "high_error_rate" in rule_ids


def test_restart_count_below_threshold_does_not_trigger():
    settings = Settings()
    event = make_event(EventType.HIGH_ERROR_RATE, restart_count=1, error_rate=0.9)
    assessment = rule_engine.assess(event, settings)
    rule_ids = {r.rule_id for r in assessment.triggered_rules}
    assert "pod_restart_threshold" not in rule_ids


def test_compound_warning_bonus_applied_when_multiple_rules_fire():
    settings = Settings()
    event = make_event(
        EventType.POD_RESTART_THRESHOLD_EXCEEDED,
        restart_count=6,
        error_rate=0.09,
        latency_ms=1200,
    )
    assessment = rule_engine.assess(event, settings)
    rule_ids = {r.rule_id for r in assessment.triggered_rules}
    assert "compound_warning" in rule_ids
    expected = (
        settings.score_pod_restart
        + settings.score_high_error_rate
        + settings.score_high_latency
        + settings.score_compound_warning_bonus
    )
    assert assessment.risk_score == expected
    assert assessment.severity == Severity.CRITICAL
    assert assessment.recommended_action == RecommendedAction.ROLLBACK
    assert assessment.requires_approval is True


def test_risk_score_is_capped_at_100():
    settings = Settings(
        score_deployment_failed=100,
        score_pod_restart=100,
        score_readiness_failure=100,
    )
    event = make_event(EventType.DEPLOYMENT_FAILED, restart_count=100)
    assessment = rule_engine.assess(event, settings)
    assert assessment.risk_score == 100


def test_readiness_probe_failure_alone_is_warning_not_high():
    settings = Settings()
    event = make_event(EventType.READINESS_PROBE_FAILURE)
    assessment = rule_engine.assess(event, settings)
    assert assessment.severity == Severity.WARNING
    assert assessment.recommended_action == RecommendedAction.MONITOR
    assert assessment.requires_approval is False


def test_node_warning_triggers_from_ready_ratio():
    settings = Settings()
    event = make_event(EventType.AKS_NODE_WARNING, node_count_ready=1, node_count_total=5)
    assessment = rule_engine.assess(event, settings)
    assert any(r.rule_id == "aks_node_warning" for r in assessment.triggered_rules)


def test_healthy_node_ratio_does_not_trigger_via_numeric_check():
    settings = Settings()
    event = make_event(
        EventType.HIGH_ERROR_RATE, node_count_ready=5, node_count_total=5, error_rate=0.5
    )
    assessment = rule_engine.assess(event, settings)
    rule_ids = {r.rule_id for r in assessment.triggered_rules}
    assert "aks_node_warning" not in rule_ids


def test_recovery_events_are_always_zero_risk():
    settings = Settings()
    for event_type in (EventType.APPLICATION_RECOVERED, EventType.ROLLBACK_COMPLETED):
        event = make_event(event_type)
        assessment = rule_engine.assess(event, settings)
        assert assessment.risk_score == 0
        assert assessment.severity == Severity.INFO
        assert assessment.recommended_action == RecommendedAction.ACKNOWLEDGE_RECOVERY


def test_explanation_lists_triggered_rule_ids():
    settings = Settings()
    event = make_event(EventType.DEPLOYMENT_FAILED)
    assessment = rule_engine.assess(event, settings)
    assert "deployment_failed" in assessment.explanation
