"""Deterministic, explainable risk assessment.

This is the only place risk is calculated. Every rule is a small, pure
function of (event, settings) -> optional TriggeredRule, so the full set of
rules can be unit tested in isolation and the total score is always the sum
of what is returned here plus the documented compound-warning bonus.
"""

from __future__ import annotations

from app.core.config import Settings
from app.models.assessment import RiskAssessment, TriggeredRule
from app.models.enums import (
    ACTIONS_REQUIRING_APPROVAL,
    EventType,
    RecommendedAction,
    Severity,
)
from app.models.events import OperationalEvent

RECOVERY_EVENT_TYPES = frozenset({EventType.APPLICATION_RECOVERED, EventType.ROLLBACK_COMPLETED})
NEUTRAL_EVENT_TYPES = frozenset({EventType.DEPLOYMENT_SUCCEEDED}) | RECOVERY_EVENT_TYPES


def _rule_deployment_failed(event: OperationalEvent, settings: Settings) -> TriggeredRule | None:
    if event.event_type != EventType.DEPLOYMENT_FAILED:
        return None
    return TriggeredRule(
        rule_id="deployment_failed",
        description="Deployment failed, which directly threatens service availability.",
        score_delta=settings.score_deployment_failed,
    )


def _rule_pod_restarts(event: OperationalEvent, settings: Settings) -> TriggeredRule | None:
    restart_count = event.payload.restart_count
    triggers_by_type = event.event_type == EventType.POD_RESTART_THRESHOLD_EXCEEDED
    triggers_by_count = (
        restart_count is not None and restart_count >= settings.restart_count_threshold
    )
    if not (triggers_by_type or triggers_by_count):
        return None
    return TriggeredRule(
        rule_id="pod_restart_threshold",
        description=(
            f"Pod restart count ({restart_count}) reached or exceeded the configured "
            f"threshold ({settings.restart_count_threshold}), indicating crash-looping."
        ),
        score_delta=settings.score_pod_restart,
    )


def _rule_readiness_failure(event: OperationalEvent, settings: Settings) -> TriggeredRule | None:
    if event.event_type != EventType.READINESS_PROBE_FAILURE:
        return None
    return TriggeredRule(
        rule_id="readiness_probe_failure",
        description="Readiness probe failure means the workload cannot safely receive traffic.",
        score_delta=settings.score_readiness_failure,
    )


def _rule_high_error_rate(event: OperationalEvent, settings: Settings) -> TriggeredRule | None:
    error_rate = event.payload.error_rate
    triggers = event.event_type == EventType.HIGH_ERROR_RATE or (
        error_rate is not None and error_rate >= settings.error_rate_threshold
    )
    if not triggers:
        return None
    return TriggeredRule(
        rule_id="high_error_rate",
        description=(
            f"Error rate ({error_rate}) is at or above the configured threshold "
            f"({settings.error_rate_threshold})."
        ),
        score_delta=settings.score_high_error_rate,
    )


def _rule_high_latency(event: OperationalEvent, settings: Settings) -> TriggeredRule | None:
    latency_ms = event.payload.latency_ms
    triggers = event.event_type == EventType.HIGH_RESPONSE_LATENCY or (
        latency_ms is not None and latency_ms >= settings.latency_threshold_ms
    )
    if not triggers:
        return None
    return TriggeredRule(
        rule_id="high_latency",
        description=(
            f"Response latency ({latency_ms} ms) is at or above the configured threshold "
            f"({settings.latency_threshold_ms} ms)."
        ),
        score_delta=settings.score_high_latency,
    )


def _rule_node_warning(event: OperationalEvent, settings: Settings) -> TriggeredRule | None:
    if event.event_type != EventType.AKS_NODE_WARNING:
        ready = event.payload.node_count_ready
        total = event.payload.node_count_total
        if ready is None or not total:
            return None
        if (ready / total) >= settings.node_ready_ratio_threshold:
            return None
    return TriggeredRule(
        rule_id="aks_node_warning",
        description="One or more AKS nodes are not ready, reducing cluster capacity.",
        score_delta=settings.score_node_warning,
    )


_RULES = (
    _rule_deployment_failed,
    _rule_pod_restarts,
    _rule_readiness_failure,
    _rule_high_error_rate,
    _rule_high_latency,
    _rule_node_warning,
)


def _severity_for_score(score: int, settings: Settings) -> Severity:
    if score >= settings.severity_critical_threshold:
        return Severity.CRITICAL
    if score >= settings.severity_high_threshold:
        return Severity.HIGH
    if score >= settings.severity_warning_threshold:
        return Severity.WARNING
    return Severity.INFO


def _recommend_action(event: OperationalEvent, severity: Severity) -> RecommendedAction:
    if event.event_type in RECOVERY_EVENT_TYPES:
        return RecommendedAction.ACKNOWLEDGE_RECOVERY
    if event.event_type in NEUTRAL_EVENT_TYPES:
        return RecommendedAction.NONE
    return {
        Severity.INFO: RecommendedAction.NONE,
        Severity.WARNING: RecommendedAction.MONITOR,
        Severity.HIGH: RecommendedAction.INVESTIGATE,
        Severity.CRITICAL: RecommendedAction.ROLLBACK,
    }[severity]


def assess(event: OperationalEvent, settings: Settings) -> RiskAssessment:
    """Evaluate one event against every rule and produce a full explanation.

    Recovery events (application_recovered, rollback_completed) and a
    successful deployment always reset risk to zero: they represent a
    confirmed return to a healthy state, which is itself a documented rule
    rather than a special case bolted onto the score.
    """
    if event.event_type in NEUTRAL_EVENT_TYPES:
        severity = Severity.INFO
        action = _recommend_action(event, severity)
        return RiskAssessment(
            event_id=event.id,
            risk_score=0,
            severity=severity,
            triggered_rules=[],
            explanation="No risk rules apply: this event reports a healthy or recovered state.",
            recommended_action=action,
            requires_approval=False,
        )

    triggered = [rule(event, settings) for rule in _RULES]
    triggered_rules = [r for r in triggered if r is not None]

    score = sum(r.score_delta for r in triggered_rules)
    if len(triggered_rules) >= 2:
        triggered_rules.append(
            TriggeredRule(
                rule_id="compound_warning",
                description=(
                    f"{len(triggered_rules)} independent warning indicators fired "
                    "simultaneously, which compounds operational risk."
                ),
                score_delta=settings.score_compound_warning_bonus,
            )
        )
        score += settings.score_compound_warning_bonus

    score = min(score, 100)
    severity = _severity_for_score(score, settings)
    action = _recommend_action(event, severity)
    requires_approval = action in ACTIONS_REQUIRING_APPROVAL

    if triggered_rules:
        explanation = "Triggered rules: " + "; ".join(
            f"[{r.rule_id}] {r.description}" for r in triggered_rules
        )
    else:
        explanation = "No risk rules triggered for this event."

    return RiskAssessment(
        event_id=event.id,
        risk_score=score,
        severity=severity,
        triggered_rules=triggered_rules,
        explanation=explanation,
        recommended_action=action,
        requires_approval=requires_approval,
    )
