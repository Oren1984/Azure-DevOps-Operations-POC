from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.enums import EventType
from app.models.events import EventPayload, OperationalEventCreate


def test_valid_event_create():
    event = OperationalEventCreate(event_type=EventType.DEPLOYMENT_FAILED, source="svc-a")
    assert event.event_type == EventType.DEPLOYMENT_FAILED


def test_unknown_event_type_is_rejected():
    with pytest.raises(ValidationError):
        OperationalEventCreate(event_type="not_a_real_type", source="svc-a")


def test_empty_source_is_rejected():
    with pytest.raises(ValidationError):
        OperationalEventCreate(event_type=EventType.DEPLOYMENT_FAILED, source="")


def test_error_rate_out_of_range_is_rejected():
    with pytest.raises(ValidationError):
        EventPayload(error_rate=1.5)


def test_negative_latency_is_rejected():
    with pytest.raises(ValidationError):
        EventPayload(latency_ms=-1)


def test_payload_defaults_are_all_none():
    payload = EventPayload()
    assert payload.model_dump(exclude_none=True) == {}
