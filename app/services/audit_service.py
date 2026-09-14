"""Small helper so every service records audit entries the same way."""

from __future__ import annotations

from typing import Any

from app.models.audit import AuditRecord
from app.models.enums import AuditAction
from app.repositories.base import AuditRepository


class AuditService:
    def __init__(self, repository: AuditRepository) -> None:
        self._repository = repository

    def record(
        self,
        *,
        correlation_id: str,
        entity_type: str,
        entity_id: str,
        action: AuditAction,
        actor: str,
        result: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditRecord:
        record = AuditRecord(
            correlation_id=correlation_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor,
            result=result,
            metadata=metadata or {},
        )
        self._repository.save(record)
        return record

    def history(self, correlation_id: str | None = None, limit: int = 500) -> list[AuditRecord]:
        return self._repository.list(correlation_id=correlation_id, limit=limit)
