"""Tests for the server-rendered local demonstration dashboard.

These only check that the dashboard route renders the expected HTML and that
the pages/endpoints it links to and calls remain reachable - the actual demo
logic is exercised by tests/e2e/test_demo_flow.py, not duplicated here.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_root_returns_html_dashboard(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_dashboard_contains_mock_demo_action(client: TestClient):
    response = client.get("/")
    body = response.text
    assert "Run MOCK Demo" in body
    assert "Local Demonstration Dashboard" in body
    assert "Deterministic MOCK Data" in body
    assert "No real Azure resources are created or modified" in body


def test_dashboard_links_to_docs_redoc_and_operational_endpoints(client: TestClient):
    body = client.get("/").text
    for href in ("/docs", "/redoc", "/health", "/ready", "/metrics"):
        assert f'href="{href}"' in body


def test_dashboard_calls_existing_demo_endpoint_not_a_new_one(client: TestClient):
    body = client.get("/").text
    assert "/api/v1/demo/run" in body
    assert "/api/v1/audit" in body


def test_docs_redoc_health_ready_metrics_still_reachable(client: TestClient):
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200
    assert client.get("/metrics").status_code == 200


def test_demo_endpoint_still_works_independently_of_dashboard(client: TestClient):
    response = client.post("/api/v1/demo/run")
    assert response.status_code == 200
    body = response.json()
    assert body["audit_trail_count"] >= 10
    assert len(body["steps"]) == 6
