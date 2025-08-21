# models — Data models and Pydantic schemas

This folder contains Pydantic data models used across the project to validate and structure data passed between the API and automation layers.

Files

- `visitor.py` 
  - Contains the primary Pydantic models used in the project:
    - `VehicleData` — data model for vehicle information (number plate, VIN, make, model, etc.)
    - `CredentialData` — data model for access credential payloads (reader type, identifier, PIN, dates, expiry, etc.)
    - `VisitorData` — data model for visitor personal information used in the automation flows
  - These models are primarily used when constructing typed payloads for automations or when validating incoming request bodies in the API.

Notes

- The models in this folder are currently designed for backward compatibility and may not include every field returned by the EVTrack UI. When adding new fields, prefer using Pydantic `Optional[...]` fields and keep default values where appropriate.
- If you plan to add OpenAPI request/response models, keep the Pydantic models in `models/` synchronized with `api/openapi.yaml`.
