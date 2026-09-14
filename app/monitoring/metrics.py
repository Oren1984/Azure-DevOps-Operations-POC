"""Prometheus-compatible metrics.

Each Container owns its own CollectorRegistry so tests can create isolated
instances instead of sharing prometheus_client's global default registry.
Locally these are scraped from GET /metrics; in AKS the same endpoint would
be scraped by Azure Monitor managed Prometheus - see docs/AZURE_ARCHITECTURE.md.
"""

from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Histogram


class Metrics:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()

        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "path", "status"],
            registry=self.registry,
        )
        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request latency in seconds",
            ["method", "path"],
            registry=self.registry,
        )
        self.errors_total = Counter(
            "errors_total",
            "Total unhandled request errors (5xx)",
            ["path"],
            registry=self.registry,
        )
        self.events_received_total = Counter(
            "events_received_total",
            "Operational events received",
            ["event_type"],
            registry=self.registry,
        )
        self.assessments_total = Counter(
            "assessments_total",
            "Risk assessments produced",
            ["severity"],
            registry=self.registry,
        )
        self.approval_decisions_total = Counter(
            "approval_decisions_total",
            "Human approval decisions recorded",
            ["decision"],
            registry=self.registry,
        )
        self.ai_fallback_total = Counter(
            "ai_fallback_total",
            "Times the AI assistant fell back to the deterministic implementation",
            registry=self.registry,
        )
