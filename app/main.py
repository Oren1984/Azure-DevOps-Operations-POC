"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.middleware import ObservabilityMiddleware
from app.api.routes import audit, dashboard, demo, events, health, incidents
from app.core.config import Settings, get_settings
from app.core.container import Container
from app.core.errors import ConflictError, NotFoundError
from app.core.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app with an eagerly-constructed Container.

    The container (settings, database, metrics registry, services) is built
    synchronously at app-creation time rather than in a lifespan hook, so a
    plain ``TestClient(app)`` works without needing the lifespan context
    manager, and the observability middleware can be wired to the same
    metrics registry the rest of the app uses.
    """
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    container = Container.build(settings)

    app = FastAPI(
        title="Azure DevOps Operations POC",
        description=(
            "Personal reference POC: turns deployment and infrastructure events into "
            "explainable, deterministic risk assessments and human-approved operational decisions. "
            "Not deployed to Azure; runs entirely locally."
        ),
        version="0.1.0",
    )
    app.state.container = container

    app.add_middleware(ObservabilityMiddleware, metrics=container.metrics)

    app.include_router(dashboard.router)
    app.include_router(health.router)
    app.include_router(events.router)
    app.include_router(incidents.router)
    app.include_router(audit.router)
    app.include_router(demo.router)

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def conflict_handler(request, exc: ConflictError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    return app


app = create_app()
