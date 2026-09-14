from __future__ import annotations

from fastapi.testclient import TestClient


def _create_high_risk_incident(client: TestClient, source: str = "svc-critical") -> str:
    response = client.post(
        "/api/v1/events",
        json={
            "event_type": "pod_restart_threshold_exceeded",
            "source": source,
            "payload": {"restart_count": 6, "error_rate": 0.09, "latency_ms": 1200},
        },
    )
    incident_id = response.json()["incident_id"]
    assert incident_id is not None
    return incident_id


def test_approve_incident(client: TestClient):
    incident_id = _create_high_risk_incident(client)
    response = client.post(
        f"/api/v1/incidents/{incident_id}/approve",
        json={"actor": "operator-1", "reason": "confirmed rollback needed"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["approval_status"] == "approved"
    assert body["decided_by"] == "operator-1"


def test_reject_incident(client: TestClient):
    incident_id = _create_high_risk_incident(client, source="svc-reject")
    response = client.post(
        f"/api/v1/incidents/{incident_id}/reject",
        json={"actor": "operator-2", "reason": "false positive"},
    )
    assert response.status_code == 200
    assert response.json()["approval_status"] == "rejected"


def test_duplicate_decision_returns_conflict(client: TestClient):
    incident_id = _create_high_risk_incident(client, source="svc-duplicate")
    client.post(f"/api/v1/incidents/{incident_id}/approve", json={"actor": "operator-1"})
    response = client.post(f"/api/v1/incidents/{incident_id}/approve", json={"actor": "operator-1"})
    assert response.status_code == 409


def test_approve_missing_incident_returns_404(client: TestClient):
    response = client.post("/api/v1/incidents/does-not-exist/approve", json={"actor": "operator-1"})
    assert response.status_code == 404


def test_get_incident_by_id(client: TestClient):
    incident_id = _create_high_risk_incident(client, source="svc-get")
    response = client.get(f"/api/v1/incidents/{incident_id}")
    assert response.status_code == 200
    assert response.json()["id"] == incident_id
