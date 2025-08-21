# automation — EVTrack browser automation helpers

This folder contains the browser automation modules used by the API to interact with the EVTrack web application. They encapsulate common workflows (login, search, create/update visitor, add credentials, invitations, vehicle management, badge generation, etc.) and are implemented using a Selenium-based webdriver started by utilities in `utils/`.

Quick notes
- Each module exposes one or more automation classes (e.g. `VisitorAutomation`, `InvitationAutomation`, `EvTrackLogin`) that perform a focused task against the EVTrack UI.
- These classes are designed to be used from async FastAPI endpoints in `api/main.py`. Some helper calls are synchronous — check individual modules.
- Several modules accept a `websocket` or provide `set_websocket(...)` to push status updates back to a connected client (used by the `/ws` endpoint in the API).
- Running these modules requires a working Selenium webdriver (Chrome/Chromium or other) and matching driver binary. See `utils/` for driver startup helpers (headless, lambda-specific helpers, etc.).

Files

- `__init__.py`
  - Package init file. May re-export frequently used automation classes or keep package metadata.

- `badges.py`
  - Functions and/or a class for generating visitor badges. Responsible for navigating to the visitor profile or badge UI, triggering badge generation/export and returning the generated content (often base64 encoded or saved to disk). Used by the API badge endpoints.

- `credentials.py`
  - Automation for adding and updating access credentials for a visitor. Includes functions to search for a visitor, open their credential tab, create/edit credential records and handle form validation messaging.

- `invitation.py`
  - Automation for sending invitations to visitors. Handles searching for a visitor, opening the invitation UI, applying invite settings (location, reason, activation/expiry) and sending the invitation. Supports status messages via websocket when available.

- `login.py`
  - `EvTrackLogin` encapsulates the login procedure for EVTrack (navigating to the login page, entering credentials, handling MFA or redirects where necessary). Typically called before other automations that require an authenticated session.

- `vehicle_add.py`
  - Automation to add a new vehicle record to EVTrack. Handles the vehicle add flow (search context, filling vehicle fields, validating required fields like VIN or number plate) and returns a success/failure result.

- `vehicle_update.py`
  - Automation to update an existing vehicle's details. Finds the vehicle in the vehicle list or via search and updates only supplied fields, returning which fields were changed.

- `vehicles.py`
  - Utility functions and helpers for interacting with the vehicle list page. May contain shared selectors, common navigation helpers or batch operations used by add/update automations.

- `visitor_add.py`
  - Automation for creating a new visitor. Fills the create visitor form, uploads any photos/documents if required, saves the visitor and returns the visitor UUID/ID.

- `visitor_create_update.py`
  - High-level automation that unifies create and update flows (create if not found, otherwise update). Useful for bulk imports and Google Sheets integration where the logic should be "upsert" style.

- `visitor_details.py`
  - Reads detailed information from a visitor's profile (profile tab, visits, credentials, documents) and returns a structured dictionary. Used by profile endpoints in the API.

- `visitor_search.py`
  - Robust visitor search helpers. Contains case-insensitive search strategies, fallback search methods and routines that return search results, UUIDs and direct profile URLs.

- `visitors.py`
  - Helpers for list-based visitor operations (get list, paging, bulk summaries). Often used by endpoints that need a fast summary rather than a full profile.

Usage & running notes

- Start a webdriver using helpers in `utils/` (e.g. `start_driver(headless=True)`) and pass the driver instance to automation classes.
  - Example pattern used across the API endpoints:
    - driver = start_driver(headless=HEADLESS_MODE)
    - login = EvTrackLogin(driver)
    - await login.login(EVTRACK_EMAIL, EVTRACK_PASSWORD)
    - automation = VisitorAutomation(driver)
    - result = await automation.create_update_visitor(visitor_data)

- When writing new automation, prefer:
  - Small focused classes or methods per workflow (search, open profile, edit, save)
  - Clear return values with success boolean and message/error fields
  - Defensive waits (explicit waits for elements) and robust selectors
  - Logging of key actions and errors for easier troubleshooting

