from __future__ import annotations

from fastapi.testclient import TestClient


def test_submit_event_returns_assessment(client: TestClient):
    response = client.post(
        "/api/v1/events",
        json={"event_type": "deployment_failed", "source": "svc-a", "payload": {}},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["event"]["event_type"] == "deployment_failed"
    assert body["assessment"]["severity"] == "high"
    assert body["incident_id"] is not None


def test_submit_event_rejects_unknown_event_type(client: TestClient):
    response = client.post(
        "/api/v1/events",
        json={"event_type": "not_a_real_event", "source": "svc-a", "payload": {}},
    )
    assert response.status_code == 422


def test_submit_event_rejects_missing_source(client: TestClient):
    response = client.post(
        "/api/v1/events",
        json={"event_type": "deployment_failed", "payload": {}},
    )
    assert response.status_code == 422


def test_get_event_by_id(client: TestClient):
    submit = client.post(
        "/api/v1/events",
        json={"event_type": "high_error_rate", "source": "svc-b", "payload": {"error_rate": 0.2}},
    )
    event_id = submit.json()["event"]["id"]

    response = client.get(f"/api/v1/events/{event_id}")
    assert response.status_code == 200
    assert response.json()["id"] == event_id


def test_get_event_missing_returns_404(client: TestClient):
    response = client.get("/api/v1/events/does-not-exist")
    assert response.status_code == 404


def test_list_events_returns_submitted_events(client: TestClient):
    client.post(
        "/api/v1/events",
        json={"event_type": "deployment_succeeded", "source": "svc-c", "payload": {}},
    )
    response = client.get("/api/v1/events")
    assert response.status_code == 200
    assert len(response.json()) >= 1
