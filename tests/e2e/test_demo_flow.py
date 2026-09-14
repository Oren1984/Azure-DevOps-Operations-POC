"""End-to-end test of the deterministic demo scenario, driven through the
same HTTP API a real client would use - no cloud access, no credentials.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_demo_runs_full_incident_lifecycle(client: TestClient):
    response = client.post("/api/v1/demo/run")
    assert response.status_code == 200
    body = response.json()

    step_names = [s["name"] for s in body["steps"]]
    assert step_names == [
        "healthy_baseline",
        "deployment_failed",
        "readiness_probe_failure",
        "compounding_warning_signals",
        "rollback_completed",
        "application_recovered",
    ]

    severities = {s["name"]: s["assessment"]["severity"] for s in body["steps"]}
    assert severities["healthy_baseline"] == "info"
    assert severities["deployment_failed"] == "high"
    assert severities["compounding_warning_signals"] == "critical"
    assert severities["rollback_completed"] == "info"
    assert severities["application_recovered"] == "info"

    critical_step = next(s for s in body["steps"] if s["name"] == "compounding_warning_signals")
    assert critical_step["assessment"]["recommended_action"] == "rollback"
    assert critical_step["assessment"]["requires_approval"] is True
    assert len(critical_step["assessment"]["triggered_rules"]) >= 3

    final_incident = body["final_incident"]
    assert final_incident is not None
    assert final_incident["approval_status"] == "approved"
    assert final_incident["resolved"] is True
    assert final_incident["decided_by"] == "demo-operator"

    assert body["audit_trail_count"] >= 10

    audit_response = client.get("/api/v1/audit", params={"correlation_id": body["correlation_id"]})
    assert audit_response.status_code == 200
    audit_records = audit_response.json()
    actions = [r["action"] for r in audit_records]
    for expected_action in (
        "event_received",
        "assessment_generated",
        "incident_opened",
        "ai_summary_requested",
        "approval_requested",
        "approval_granted",
        "incident_resolved",
        "demo_scenario_completed",
    ):
        assert expected_action in actions, f"missing audit action: {expected_action}"
