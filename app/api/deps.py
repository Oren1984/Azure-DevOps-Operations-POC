"""FastAPI dependency accessors for the request-scoped container."""

from __future__ import annotations

from fastapi import Request

from app.core.container import Container
from app.services.audit_service import AuditService
from app.services.demo_service import DemoService
from app.services.event_service import EventService
from app.services.incident_service import IncidentService


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_event_service(request: Request) -> EventService:
    return get_container(request).event_service


def get_incident_service(request: Request) -> IncidentService:
    return get_container(request).incident_service


def get_audit_service(request: Request) -> AuditService:
    return get_container(request).audit_service


def get_demo_service(request: Request) -> DemoService:
    return get_container(request).demo_service
