from __future__ import annotations

import pytest

from app.core.config import Settings
from app.domain import rule_engine
from app.models.audit import AuditRecord
from app.models.enums import ApprovalStatus, AuditAction, EventType
from app.models.incident import IncidentRecord
from app.repositories.database import Database
from app.repositories.sqlite_repository import (
    SqliteAuditRepository,
    SqliteEventRepository,
    SqliteIncidentRepository,
)
from tests.unit.test_rule_engine import make_event  # reuse event factory


@pytest.fixture
def db() -> Database:
    return Database(":memory:")


def test_event_repository_round_trip(db: Database):
    repo = SqliteEventRepository(db)
    event = make_event(EventType.DEPLOYMENT_FAILED)
    repo.save(event)
    fetched = repo.get(event.id)
    assert fetched is not None
    assert fetched.id == event.id
    assert fetched.event_type == EventType.DEPLOYMENT_FAILED


def test_event_repository_get_missing_returns_none(db: Database):
    repo = SqliteEventRepository(db)
    assert repo.get("does-not-exist") is None


def test_event_repository_list_orders_most_recent_first(db: Database):
    repo = SqliteEventRepository(db)
    first = make_event(EventType.DEPLOYMENT_SUCCEEDED)
    repo.save(first)
    second = make_event(EventType.DEPLOYMENT_FAILED)
    repo.save(second)
    events = repo.list(limit=10)
    assert events[0].id == second.id


def test_incident_repository_find_active_by_source(db: Database):
    repo = SqliteIncidentRepository(db)
    settings = Settings()
    event = make_event(EventType.DEPLOYMENT_FAILED)
    assessment = rule_engine.assess(event, settings)
    incident = IncidentRecord(
        source=event.source,
        event_id=event.id,
        assessment=assessment,
        approval_status=ApprovalStatus.NOT_REQUIRED,
    )
    repo.save(incident)

    active = repo.find_active_by_source(event.source)
    assert active is not None
    assert active.id == incident.id

    incident.resolved = True
    repo.save(incident)
    assert repo.find_active_by_source(event.source) is None


def test_audit_repository_filters_by_correlation_id(db: Database):
    repo = SqliteAuditRepository(db)
    repo.save(
        AuditRecord(
            correlation_id="corr-1",
            entity_type="event",
            entity_id="e1",
            action=AuditAction.EVENT_RECEIVED,
            actor="api",
            result="stored",
        )
    )
    repo.save(
        AuditRecord(
            correlation_id="corr-2",
            entity_type="event",
            entity_id="e2",
            action=AuditAction.EVENT_RECEIVED,
            actor="api",
            result="stored",
        )
    )
    records = repo.list(correlation_id="corr-1")
    assert len(records) == 1
    assert records[0].entity_id == "e1"
