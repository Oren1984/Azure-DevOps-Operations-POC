"""Repository abstractions. Storage can be swapped without touching services."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.audit import AuditRecord
from app.models.events import OperationalEvent
from app.models.incident import IncidentRecord


class EventRepository(ABC):
    @abstractmethod
    def save(self, event: OperationalEvent) -> None: ...

    @abstractmethod
    def get(self, event_id: str) -> OperationalEvent | None: ...

    @abstractmethod
    def list(self, limit: int = 100) -> list[OperationalEvent]: ...


class IncidentRepository(ABC):
    @abstractmethod
    def save(self, incident: IncidentRecord) -> None: ...

    @abstractmethod
    def get(self, incident_id: str) -> IncidentRecord | None: ...

    @abstractmethod
    def list(self, limit: int = 100) -> list[IncidentRecord]: ...

    @abstractmethod
    def find_active_by_source(self, source: str) -> IncidentRecord | None:
        """Return the most recent unresolved incident for a source, if any."""
        ...


class AuditRepository(ABC):
    @abstractmethod
    def save(self, record: AuditRecord) -> None: ...

    @abstractmethod
    def list(self, correlation_id: str | None = None, limit: int = 500) -> list[AuditRecord]: ...
