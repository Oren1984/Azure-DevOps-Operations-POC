# Testing

## Strategy

Three layers, each testing a different boundary:

- **Unit** (`tests/unit/`) - the rule engine, AI assistant fallback behavior, Pydantic
  validation, and repository behavior, all in isolation. No HTTP, no running app.
- **Integration** (`tests/integration/`) - the FastAPI app via `TestClient`, exercising real
  routes against a real (in-memory) SQLite database, but nothing external.
- **E2E** (`tests/e2e/`) - the full demo scenario, driven through the same HTTP API a real client
  would use, asserting on the entire incident lifecycle and the resulting audit trail.

All 58 tests are deterministic and require no internet access, no Azure credentials, and no paid
services - every test uses `Settings(database_path=":memory:")` (see `tests/conftest.py`).

## Running the tests

```bash
pip install -r requirements-dev.txt
pytest -q                     # everything
pytest tests/unit -q          # one layer
pytest -q -k demo             # by keyword
```

## What each layer covers

| Layer | File | Covers |
|---|---|---|
| Unit | `test_rule_engine.py` | Every scoring rule, severity thresholds, the compound-warning bonus, score capping, recovery events, action recommendation, approval requirement |
| Unit | `test_ai_assistant.py` | Deterministic assistant output, Pydantic schema rejection of empty summary/steps, fallback on timeout / malformed response / missing config, factory defaults |
| Unit | `test_repositories.py` | SQLite round-trips for events/incidents/audit records, missing-record lookups, active-incident-by-source queries |
| Unit | `test_event_validation.py` | Rejection of unknown event types, empty source, out-of-range payload values |
| Unit | `test_event_service.py` | Incident open/escalate/resolve transitions, repository-failure propagation |
| Integration | `test_api_events.py` | Event submission, 422 on invalid input, 404 on missing event, listing |
| Integration | `test_api_incidents.py` | Approve, reject, 409 on a duplicate decision, 404 on a missing incident |
| Integration | `test_api_health_and_metrics.py` | `/health`, `/ready`, `/metrics` content, `/api/v1/audit` filtering |
| Integration | `test_dashboard.py` | `GET /` returns HTML containing the "Run MOCK Demo" action, links to `/docs`/`/redoc`/`/health`/`/ready`/`/metrics`, and that `/docs`, `/redoc`, and `POST /api/v1/demo/run` keep working independently of the dashboard |
| E2E | `test_demo_flow.py` | The full incident lifecycle end to end, plus every expected audit action appearing in the trail |

## Mocked cloud dependencies

There are none to mock in the default path - the app runs entirely offline. The one place a
cloud dependency *could* exist is the optional Azure OpenAI assistant
(`app/integrations/ai_assistant.py`); it is tested by injecting fake primary assistants that
raise `httpx.TimeoutException` or `KeyError` (simulating a malformed response), never by making a
real network call.

## Known limitations

- Coverage is meaningful but not exhaustive - this is a POC, not a project with a coverage gate.
- The Azure OpenAI adapter's HTTP call itself (`AzureOpenAIIncidentAssistant.summarize`) is not
  unit-tested against a mocked HTTP transport; only its configuration-validation and the
  fallback wrapper around it are tested. It is explicitly illustrative code (see
  `app/integrations/ai_assistant.py`'s module docstring), not a path this project depends on.
- Terraform and Kubernetes manifests are checked for formatting/syntax, not exercised by the
  Python test suite - see the verification steps in the root `README.md` for how those are
  validated instead.
