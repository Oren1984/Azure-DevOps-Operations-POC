# Demo

## Story

A service called `checkout-service` has a bad day: a deployment fails, its readiness probe
starts failing, and then pods start crash-looping while error rate and latency both spike at
once. The system escalates this into a CRITICAL incident recommending a rollback, which requires
a human decision before anything would actually happen. A human approves it, the rollback is
simulated as completed, and the service is confirmed recovered. Every step is recorded in the
audit trail.

## Browser-based demo (dashboard)

Start the app (either directly or via Docker Compose), then open
**`http://localhost:8000/`** in a browser.

This is the **local demonstration dashboard** - a thin, server-rendered page
(`app/templates/dashboard.html`) that exists only to make the flow below easier to see. It is
explicitly labeled "Local Demonstration Dashboard" / "Deterministic MOCK Data" on the page itself,
and it creates or modifies nothing in Azure. It is **not** an operations portal: it has one
button, no write path of its own, and no logic beyond calling the same two API endpoints
described below and rendering their JSON.

1. Click **"Run MOCK Demo"**.
2. The page calls `POST /api/v1/demo/run` (shows a loading state), then
   `GET /api/v1/audit?correlation_id=<the demo's correlation ID>` to fetch the full audit trail
   for that run.
3. Results render in four sections:
   - **Summary cards** - event count, incident count, approval status, audit record count.
   - **Incident details** - the final incident's ID, severity/risk score, explanation,
     recommended action, and approval/resolution state.
   - **Workflow steps** - the actual audit trail actions in order (`event_received`,
     `assessment_generated`, `incident_opened`, `ai_summary_requested`, `approval_requested`,
     `approval_granted`, `incident_resolved`, `demo_scenario_completed`).
   - **Audit trail table** and an expandable **raw JSON** block (the exact API responses, for
     technical inspection).
4. Re-clicking "Run MOCK Demo" runs the scenario again (a fresh event/incident each time - the
   underlying demo is deterministic in its logic, not idempotent in its IDs).
5. If the API call fails for any reason, the page shows an error state instead of stale or
   fabricated data.

Small navigation links at the top of the dashboard go to Swagger (`/docs`), ReDoc (`/redoc`),
`/health`, `/ready`, and `/metrics` - all unchanged and still fully functional.

## Command-line demo

```bash
curl -X POST http://localhost:8000/api/v1/demo/run | python -m json.tool
```

Or run the same logic directly in Python without an HTTP server:

```bash
python -c "
from app.core.config import Settings
from app.core.container import Container
c = Container.build(Settings(database_path=':memory:'))
result = c.demo_service.run()
for step in result.steps:
    a = step.outcome.assessment
    print(f'{step.name:30s} severity={a.severity.value:8s} score={a.risk_score:3d} action={a.recommended_action.value}')
"
```

## Expected output

Six steps, in order, with these severities:

| Step | Event type | Severity | Notes |
|---|---|---|---|
| `healthy_baseline` | `deployment_succeeded` | `info` | Establishes a healthy starting point |
| `deployment_failed` | `deployment_failed` | `high` | Opens an incident; action `investigate`, no approval needed yet |
| `readiness_probe_failure` | `readiness_probe_failure` | `warning` | Recorded, but alone stays below the incident-opening threshold |
| `compounding_warning_signals` | `pod_restart_threshold_exceeded` (with elevated error rate and latency in the same event) | `critical` | Escalates the existing incident; action `rollback`, **requires approval** |
| `rollback_completed` | `rollback_completed` | `info` | A human has already approved; this resolves the incident |
| `application_recovered` | `application_recovered` | `info` | Confirms recovery |

The response also includes `final_incident` (approved, resolved) and `audit_trail_count` (at
least 10 records - one call to `GET /api/v1/audit?correlation_id=<the demo's correlation_id>`
returns the full ordered trail).

## What this proves

- The rule engine is **deterministic**: the same sequence of inputs always produces the same
  scores, severities, and recommended actions (`app/domain/rule_engine.py` takes no random or
  time-dependent input into its scoring).
- **Compounding signals matter**: three independent warning indicators arriving together
  (restart count, error rate, latency) push the score past the CRITICAL threshold and add a
  documented "compound warning" bonus - this is a named, inspectable rule, not a hidden
  heuristic.
- **A disruptive action never happens automatically**: the incident sits at `PENDING` until
  `IncidentService.approve()` (via `POST /api/v1/incidents/{id}/approve`) is called - the demo
  calls this itself, standing in for a human, but the code path is identical to a real operator
  clicking approve.
- **Everything is audited**: `event_received`, `assessment_generated`, `incident_opened`,
  `ai_summary_requested`, `approval_requested`, `approval_granted`, `incident_resolved`, and
  `demo_scenario_completed` all appear in the trail for one correlation ID, in order.
- **The optional AI path is safe by default**: the incident's `ai_summary.source` is
  `"deterministic"` unless `APP_AI_PROVIDER=azure_openai` is explicitly configured, and even then
  it can only ever produce a summary + suggested steps - never an action.
- **The dashboard adds no new behavior**: it is a presentation layer only, calling the same
  `POST /api/v1/demo/run` and `GET /api/v1/audit` endpoints already covered above and by
  `tests/e2e/test_demo_flow.py`. Whatever it displays is exactly what those endpoints returned -
  a local, deterministic MOCK demonstration, never a real Azure operation.
