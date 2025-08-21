Google Apps Script integration for EVTrack

Purpose

This folder contains Google Apps Script (GAS) code that runs inside Google Sheets to integrate with the EVTrack API for bulk visitor processing, sheet exports, and Drive photo processing. These scripts are optional — the main project and API function without them. Keep them as a safe reference until you decide to enable Sheets automation.

Files included

- `sheets_integration.js` — helpers to parse sheet rows into EVTrack visitor payloads, validate sheet structure, and produce export-ready 2D arrays. (Will prob be replaced since its not too accurate)
- `main_workflows.js` — user-facing workflows (menu items) that call the helper functions to create/update/search visitors from a sheet, and to wire up UI actions.
- `evtrack_api.js` — wrapper functions that call your EVTrack REST API (uses UrlFetchApp) and return standardized responses.
- `authentication.js` — utilities for managing API keys or OAuth tokens in script properties and adding authorization checks.
- `drive_integration.js` — helpers for extracting Drive file IDs and processing images referenced in sheet columns.

When to use

- Use these scripts when you want non-developers to process visitor data directly from Google Sheets (bulk create/update/search/export).
- Not required for core automation (Selenium or API). If you are not ready to enable Google Sheets automation, it is safe to leave these files in the repo as documentation.

Quick setup (how to get the GAS project running)

1. Prepare the backend
   - Ensure your EVTrack API is reachable and you have an API key or access token.
   - If your API uses an API key, consider creating a limited-scope key for Sheets usage.

2. Create a new Apps Script project
   - Open the Google Sheet you will use, then: Extensions → Apps Script.
   - Create script files matching the filenames above and paste the corresponding code from this repo into each file.

3. Configure script properties
   - Open Project Settings → Script properties or use the `PropertiesService` API in code.
   - Add at least:
     - `API_BASE_URL` — full URL of your EVTrack API (e.g., `https://api.example.com`)
     - `API_KEY` — the API key to authenticate requests (or leave blank if you will use OAuth)
   - Optional: `SERVICE_ACCOUNT_EMAIL`, `OAUTH_CLIENT_ID` if you plan a server-to-server flow.

4. Authorize and enable scopes
   - First run will prompt for authorization. The scripts use `UrlFetchApp` and may require Drive access for photo processing.
   - If Drive actions are needed, enable the Drive advanced service (if your code uses it) or grant Drive scopes when prompted.

5. Install a trigger and test
   - Implement `onOpen(e)` in `main_workflows.js` to add a custom menu to the sheet. Run `onOpen` once or open the sheet to see the menu.
   - Use menu actions to run a small test on 1–2 rows. Review the logs (Executions) and the API server logs.

6. Rate limits & delays
   - The scripts include small sleep/delay calls to avoid overwhelming the API. Keep those when processing large sheets.


The GAS helpers are tolerant of header variations (spaces/underscores/case) but sticking to the template reduces errors.

Security notes

- Keep `API_KEY` out of public repositories. Script properties are private to the script owner but avoid pasting secrets into code.
- Prefer issuing a limited-scope API key for Google Sheets usage. If you require stronger security, implement OAuth or a service account server-side and proxy requests instead of embedding credentials in the sheet.