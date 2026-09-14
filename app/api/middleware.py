"""Correlation ID propagation, structured request logging, and HTTP metrics."""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.correlation import new_correlation_id, set_correlation_id
from app.core.logging import get_logger
from app.monitoring.metrics import Metrics

logger = get_logger("app.request")

CORRELATION_HEADER = "X-Correlation-ID"


class ObservabilityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, metrics: Metrics) -> None:
        super().__init__(app)
        self._metrics = metrics

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = request.headers.get(CORRELATION_HEADER) or new_correlation_id()
        set_correlation_id(correlation_id)
        request.state.correlation_id = correlation_id

        route_path = request.url.path
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            logger.exception("unhandled_request_error", extra={"path": route_path})
            raise
        finally:
            duration = time.perf_counter() - start
            self._metrics.http_requests_total.labels(
                method=request.method, path=route_path, status=str(status_code)
            ).inc()
            self._metrics.http_request_duration_seconds.labels(
                method=request.method, path=route_path
            ).observe(duration)
            if status_code >= 500:
                self._metrics.errors_total.labels(path=route_path).inc()
            logger.info(
                "request_completed",
                extra={
                    "path": route_path,
                    "method": request.method,
                    "status_code": status_code,
                    "duration_ms": round(duration * 1000, 2),
                },
            )
