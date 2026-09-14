"""Deterministic, offline end-to-end demo endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_demo_service, get_incident_service
from app.api.schemas import DemoRunResponse, DemoStepView
from app.services.demo_service import DemoService
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])


@router.post("/run", response_model=DemoRunResponse)
def run_demo(
    demo_service: DemoService = Depends(get_demo_service),
    incident_service: IncidentService = Depends(get_incident_service),
) -> DemoRunResponse:
    result = demo_service.run()
    steps = [
        DemoStepView(
            name=step.name,
            event=step.outcome.event,
            assessment=step.outcome.assessment,
            incident_id=step.outcome.incident.id if step.outcome.incident else None,
        )
        for step in result.steps
    ]

    final_incident = None
    incident_id = next((s.incident_id for s in steps if s.incident_id), None)
    if incident_id:
        final_incident = incident_service.get(incident_id)

    return DemoRunResponse(
        correlation_id=result.correlation_id,
        steps=steps,
        final_incident=final_incident,
        audit_trail_count=len(result.audit_trail),
    )
