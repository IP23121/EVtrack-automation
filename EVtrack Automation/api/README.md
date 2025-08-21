# api — EVTrack API (folder)

This folder contains the FastAPI-based HTTP API used by the EVTrack automation project. It exposes endpoints for visitor, vehicle, credential, invitation, badge, Google Sheets and Drive integrations, plus health/auth endpoints.

Quick overview
- Language: Python 3
- Framework: FastAPI (async endpoints)
- Main entry: `main.py`

Files

- `main.py`
  - The primary FastAPI application. Declares most endpoints used by the project:
    - Visitor endpoints: search, create, update, profile, badge, invite
    - Vehicle endpoints: add, update
    - Credential endpoints: add, update
    - Authentication endpoints: `/auth/verify`, login test
    - Google Sheets & Drive integration endpoints (many currently return 501 / TODO)
    - WebSocket endpoint (`/ws`) used to stream status updates to a front-end or long‑running processes
    - Swagger/OpenAPI UI routes and a served `openapi.yaml`
  - The file contains startup/run logic (it can be executed directly; it also includes a `if __name__ == "__main__"` block that calls `uvicorn.run`).
  - Notes:
    - Many endpoints use browser automation helpers in the `automation/` package (e.g. `VisitorAutomation`, `EvTrackLogin`). These endpoints often start a webdriver, perform actions and return results.
    - Several Google Sheets / Drive related endpoints are placeholders and intentionally return 501 (Not Implemented) until integration logic is added.
    - The code references `app.state.active_websocket` for live status updates.

- `openapi.yaml`
  - The OpenAPI specification served by the API (used by integrations or to seed the Swagger UI). Keep this file in sync with `main.py` if you modify endpoint signatures.

- `__init__.py`
  - Marks this folder as a Python package. It may contain package-level imports or metadata (currently used to allow `import api` or relative imports).

Other notes and tips

- Environment variables and configuration referenced in `main.py` (ensure these are set when running the API):
  - `EVTRACK_EMAIL`, `EVTRACK_PASSWORD` — credentials used by the automation to log in to EVTrack
  - `COGNITO_USER_POOL_ID`, `GOOGLE_CLIENT_ID` — used for health checks and OAuth-related features
  - `VALID_API_KEYS` — API key config used by request verification

- Running locally
  - From the repository root you can run the API directly with Python (the `main.py` contains an `uvicorn.run` call when executed as script) or use uvicorn yourself:
    - python -m api.main
    - uvicorn api.main:app --reload --host 0.0.0.0 --port 3000
  - Make sure required environment variables are configured before starting the server.

- Web automation dependencies
  - The endpoints depend on the `automation/` modules and a Selenium webdriver configured by `utils/start_driver` / `utils/lambda_selenium`.
  - Running endpoints that invoke browser automation requires the correct webdriver binary and display/headless configuration.

- Testing & debugging
  - Many endpoints accept both form data (for the Swagger UI) and JSON (for programmatic calls). Check the logs for helpful debug messages which are emitted inside the endpoints.

- Contribution
  - Keep `openapi.yaml` and any changes to endpoint request/response shapes in `main.py` consistent.
  - If you add Google Sheets/Drive functionality, update the status/health endpoints and document expected payloads in `openapi.yaml`.

