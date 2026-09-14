"""SQLite implementations of the repository interfaces."""

from __future__ import annotations

from app.models.audit import AuditRecord
from app.models.events import OperationalEvent
from app.models.incident import IncidentRecord
from app.repositories.base import AuditRepository, EventRepository, IncidentRepository
from app.repositories.database import Database


class SqliteEventRepository(EventRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    def save(self, event: OperationalEvent) -> None:
        with self._db.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO events (id, data, received_at) VALUES (?, ?, ?)",
                (event.id, event.model_dump_json(), event.received_at.isoformat()),
            )

    def get(self, event_id: str) -> OperationalEvent | None:
        with self._db.connect() as conn:
            row = conn.execute("SELECT data FROM events WHERE id = ?", (event_id,)).fetchone()
        return OperationalEvent.model_validate_json(row["data"]) if row else None

    def list(self, limit: int = 100) -> list[OperationalEvent]:
        with self._db.connect() as conn:
            rows = conn.execute(
                "SELECT data FROM events ORDER BY rowid DESC LIMIT ?", (limit,)
            ).fetchall()
        return [OperationalEvent.model_validate_json(row["data"]) for row in rows]


class SqliteIncidentRepository(IncidentRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    def save(self, incident: IncidentRecord) -> None:
        with self._db.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO incidents (id, source, resolved, data, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    incident.id,
                    incident.source,
                    int(incident.resolved),
                    incident.model_dump_json(),
                    incident.updated_at.isoformat(),
                ),
            )

    def get(self, incident_id: str) -> IncidentRecord | None:
        with self._db.connect() as conn:
            row = conn.execute("SELECT data FROM incidents WHERE id = ?", (incident_id,)).fetchone()
        return IncidentRecord.model_validate_json(row["data"]) if row else None

    def list(self, limit: int = 100) -> list[IncidentRecord]:
        with self._db.connect() as conn:
            rows = conn.execute(
                "SELECT data FROM incidents ORDER BY rowid DESC LIMIT ?", (limit,)
            ).fetchall()
        return [IncidentRecord.model_validate_json(row["data"]) for row in rows]

    def find_active_by_source(self, source: str) -> IncidentRecord | None:
        with self._db.connect() as conn:
            row = conn.execute(
                "SELECT data FROM incidents WHERE source = ? AND resolved = 0 "
                "ORDER BY rowid DESC LIMIT 1",
                (source,),
            ).fetchone()
        return IncidentRecord.model_validate_json(row["data"]) if row else None


class SqliteAuditRepository(AuditRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    def save(self, record: AuditRecord) -> None:
        with self._db.connect() as conn:
            conn.execute(
                "INSERT INTO audit_records (id, correlation_id, timestamp, data) "
                "VALUES (?, ?, ?, ?)",
                (
                    record.id,
                    record.correlation_id,
                    record.timestamp.isoformat(),
                    record.model_dump_json(),
                ),
            )

    def list(self, correlation_id: str | None = None, limit: int = 500) -> list[AuditRecord]:
        with self._db.connect() as conn:
            if correlation_id:
                rows = conn.execute(
                    "SELECT data FROM audit_records WHERE correlation_id = ? "
                    "ORDER BY rowid ASC LIMIT ?",
                    (correlation_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT data FROM audit_records ORDER BY rowid DESC LIMIT ?", (limit,)
                ).fetchall()
        return [AuditRecord.model_validate_json(row["data"]) for row in rows]
