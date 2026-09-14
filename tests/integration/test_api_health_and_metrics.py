from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_ok_when_database_reachable(client: TestClient):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_metrics_endpoint_exposes_prometheus_text(client: TestClient):
    payload = {"event_type": "deployment_succeeded", "source": "svc", "payload": {}}
    client.post("/api/v1/events", json=payload)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "events_received_total" in response.text
    assert "http_requests_total" in response.text


def test_audit_endpoint_returns_records_for_correlation_id(client: TestClient):
    submit = client.post(
        "/api/v1/events",
        json={"event_type": "deployment_failed", "source": "svc-audit", "payload": {}},
        headers={"X-Correlation-ID": "corr-audit-test"},
    )
    assert submit.status_code == 201
    response = client.get("/api/v1/audit", params={"correlation_id": "corr-audit-test"})
    assert response.status_code == 200
    records = response.json()
    assert len(records) >= 2
    assert all(r["correlation_id"] == "corr-audit-test" for r in records)
