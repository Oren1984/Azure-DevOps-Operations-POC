from __future__ import annotations

import pytest

from app.core.container import Container
from app.models.enums import EventType
from app.models.events import EventPayload, OperationalEventCreate


def test_repository_failure_propagates(container: Container):
    class ExplodingRepository:
        def save(self, event):
            raise RuntimeError("simulated repository outage")

    container.event_service._events = ExplodingRepository()  # type: ignore[attr-defined]

    with pytest.raises(RuntimeError, match="simulated repository outage"):
        container.event_service.submit_event(
            OperationalEventCreate(event_type=EventType.DEPLOYMENT_FAILED, source="svc-a"),
            correlation_id="corr-1",
        )


def test_incident_opens_only_for_high_or_critical_severity(container: Container):
    outcome = container.event_service.submit_event(
        OperationalEventCreate(
            event_type=EventType.READINESS_PROBE_FAILURE,
            source="svc-warning",
            payload=EventPayload(),
        ),
        correlation_id="corr-2",
    )
    assert outcome.assessment.severity.value == "warning"
    assert outcome.incident is None


def test_incident_escalates_and_requires_approval(container: Container):
    first = container.event_service.submit_event(
        OperationalEventCreate(event_type=EventType.DEPLOYMENT_FAILED, source="svc-escalate"),
        correlation_id="corr-3",
    )
    assert first.incident is not None
    assert first.incident.approval_status.value == "not_required"

    second = container.event_service.submit_event(
        OperationalEventCreate(
            event_type=EventType.POD_RESTART_THRESHOLD_EXCEEDED,
            source="svc-escalate",
            payload=EventPayload(restart_count=6, error_rate=0.09, latency_ms=1200),
        ),
        correlation_id="corr-3",
    )
    assert second.incident is not None
    assert second.incident.id == first.incident.id
    assert second.incident.approval_status.value == "pending"
    assert second.assessment.severity.value == "critical"


def test_recovery_event_resolves_open_incident(container: Container):
    opened = container.event_service.submit_event(
        OperationalEventCreate(event_type=EventType.DEPLOYMENT_FAILED, source="svc-recover"),
        correlation_id="corr-4",
    )
    assert opened.incident is not None

    recovered = container.event_service.submit_event(
        OperationalEventCreate(event_type=EventType.ROLLBACK_COMPLETED, source="svc-recover"),
        correlation_id="corr-4",
    )
    assert recovered.incident is not None
    assert recovered.incident.resolved is True
