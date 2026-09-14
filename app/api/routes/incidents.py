"""Incident retrieval and the human approval gate.

These endpoints only ever record a decision made by a human (or the demo
script standing in for one) - they never execute a rollback, scaling, or
configuration change themselves.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.deps import get_incident_service
from app.api.schemas import ApprovalDecisionRequest
from app.core.errors import ConflictError, NotFoundError
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


@router.get("")
def list_incidents(
    limit: int = Query(default=100, ge=1, le=1000),
    incident_service: IncidentService = Depends(get_incident_service),
):
    return incident_service.list(limit=limit)


@router.get("/{incident_id}")
def get_incident(
    incident_id: str, incident_service: IncidentService = Depends(get_incident_service)
):
    try:
        return incident_service.get(incident_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{incident_id}/approve")
def approve_incident(
    incident_id: str,
    body: ApprovalDecisionRequest,
    request: Request,
    incident_service: IncidentService = Depends(get_incident_service),
):
    try:
        return incident_service.approve(
            incident_id,
            actor=body.actor,
            reason=body.reason,
            correlation_id=request.state.correlation_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{incident_id}/reject")
def reject_incident(
    incident_id: str,
    body: ApprovalDecisionRequest,
    request: Request,
    incident_service: IncidentService = Depends(get_incident_service),
):
    try:
        return incident_service.reject(
            incident_id,
            actor=body.actor,
            reason=body.reason,
            correlation_id=request.state.correlation_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
