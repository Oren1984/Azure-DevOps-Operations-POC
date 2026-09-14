"""Minimal dependency container.

No DI framework is used: FastAPI's own Depends() plus this one object,
built once at startup and stored on app.state, is enough for a project this
size. See docs/ARCHITECTURE.md for the reasoning.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings
from app.integrations.ai_assistant import build_incident_assistant
from app.monitoring.metrics import Metrics
from app.repositories.database import Database
from app.repositories.sqlite_repository import (
    SqliteAuditRepository,
    SqliteEventRepository,
    SqliteIncidentRepository,
)
from app.services.audit_service import AuditService
from app.services.demo_service import DemoService
from app.services.event_service import EventService
from app.services.incident_service import IncidentService


@dataclass
class Container:
    settings: Settings
    database: Database
    metrics: Metrics
    audit_service: AuditService
    event_service: EventService
    incident_service: IncidentService
    demo_service: DemoService

    @classmethod
    def build(cls, settings: Settings | None = None) -> Container:
        settings = settings or Settings()
        database = Database(settings.database_path)
        metrics = Metrics()

        audit_repo = SqliteAuditRepository(database)
        event_repo = SqliteEventRepository(database)
        incident_repo = SqliteIncidentRepository(database)

        audit_service = AuditService(audit_repo)
        assistant = build_incident_assistant(settings)
        event_service = EventService(
            settings, event_repo, incident_repo, audit_service, assistant, metrics
        )
        incident_service = IncidentService(incident_repo, audit_service, metrics)
        demo_service = DemoService(event_service, incident_service, audit_service)

        return cls(
            settings=settings,
            database=database,
            metrics=metrics,
            audit_service=audit_service,
            event_service=event_service,
            incident_service=incident_service,
            demo_service=demo_service,
        )
