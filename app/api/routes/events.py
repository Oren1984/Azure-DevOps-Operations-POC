"""Event submission and retrieval."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.deps import get_event_service
from app.api.schemas import EventSubmissionResponse
from app.core.errors import NotFoundError
from app.models.events import OperationalEventCreate
from app.services.event_service import EventService

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.post("", response_model=EventSubmissionResponse, status_code=status.HTTP_201_CREATED)
def submit_event(
    body: OperationalEventCreate,
    request: Request,
    event_service: EventService = Depends(get_event_service),
) -> EventSubmissionResponse:
    outcome = event_service.submit_event(body, correlation_id=request.state.correlation_id)
    return EventSubmissionResponse(
        event=outcome.event,
        assessment=outcome.assessment,
        incident_id=outcome.incident.id if outcome.incident else None,
    )


@router.get("")
def list_events(
    limit: int = Query(default=100, ge=1, le=1000),
    event_service: EventService = Depends(get_event_service),
):
    return event_service.list_events(limit=limit)


@router.get("/{event_id}")
def get_event(event_id: str, event_service: EventService = Depends(get_event_service)):
    try:
        return event_service.get_event(event_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
