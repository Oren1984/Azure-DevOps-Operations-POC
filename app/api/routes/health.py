"""Liveness, readiness, and metrics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.deps import get_container
from app.core.container import Container

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness probe: the process is up. No dependency checks."""
    return {"status": "ok"}


@router.get("/ready")
def ready(container: Container = Depends(get_container)) -> Response:
    """Readiness probe: can the app reach its own database."""
    try:
        with container.database.connect() as conn:
            conn.execute("SELECT 1")
    except Exception:
        return Response(
            status_code=503, content='{"status":"not_ready"}', media_type="application/json"
        )
    return Response(status_code=200, content='{"status":"ready"}', media_type="application/json")


@router.get("/metrics")
def metrics(container: Container = Depends(get_container)) -> Response:
    payload = generate_latest(container.metrics.registry)
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)
