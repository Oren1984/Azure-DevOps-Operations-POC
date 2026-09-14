"""Enumerations shared across the domain model."""

from enum import StrEnum


class EventType(StrEnum):
    DEPLOYMENT_SUCCEEDED = "deployment_succeeded"
    DEPLOYMENT_FAILED = "deployment_failed"
    POD_RESTART_THRESHOLD_EXCEEDED = "pod_restart_threshold_exceeded"
    READINESS_PROBE_FAILURE = "readiness_probe_failure"
    HIGH_ERROR_RATE = "high_error_rate"
    HIGH_RESPONSE_LATENCY = "high_response_latency"
    AKS_NODE_WARNING = "aks_node_warning"
    APPLICATION_RECOVERED = "application_recovered"
    ROLLBACK_COMPLETED = "rollback_completed"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendedAction(StrEnum):
    NONE = "none"
    MONITOR = "monitor"
    INVESTIGATE = "investigate"
    ROLLBACK = "rollback"
    SCALE = "scale"
    SUSPEND_DEPLOYMENT = "suspend_deployment"
    ACKNOWLEDGE_RECOVERY = "acknowledge_recovery"


# Actions with a real-world operational blast radius. The POC never executes
# these; it only ever records a human decision about them.
ACTIONS_REQUIRING_APPROVAL: frozenset[RecommendedAction] = frozenset(
    {
        RecommendedAction.ROLLBACK,
        RecommendedAction.SCALE,
        RecommendedAction.SUSPEND_DEPLOYMENT,
    }
)


class ApprovalStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AuditAction(StrEnum):
    EVENT_RECEIVED = "event_received"
    ASSESSMENT_GENERATED = "assessment_generated"
    AI_SUMMARY_REQUESTED = "ai_summary_requested"
    AI_FALLBACK_ACTIVATED = "ai_fallback_activated"
    INCIDENT_OPENED = "incident_opened"
    INCIDENT_RESOLVED = "incident_resolved"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_REJECTED = "approval_rejected"
    DEMO_SCENARIO_COMPLETED = "demo_scenario_completed"
