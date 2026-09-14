"""Read-only audit trail retrieval."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_audit_service
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("")
def list_audit_records(
    correlation_id: str | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=2000),
    audit_service: AuditService = Depends(get_audit_service),
):
    return audit_service.history(correlation_id=correlation_id, limit=limit)
