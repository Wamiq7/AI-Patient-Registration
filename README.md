# Patient Registration API

FastAPI backend for phone-based patient registration. A Vapi voice assistant collects details, then this API validates and stores them in Postgres (Neon). The model never talks to the database.

```
Caller → Vapi → create_patient tool → FastAPI → Postgres
```

IDs are UUIDs. Timestamps are UTC. Deletes are soft (`deleted_at`). An active phone number can only belong to one patient.

## Stack

Python 3.11+, FastAPI, SQLAlchemy 2, Pydantic v2, Postgres (Neon).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env
```

Put your Neon **pooled** connection string in `.env`:

```env
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST/neondb?sslmode=require
VAPI_API_KEY=
```

A Neon dashboard URL that starts with `postgresql://` is fine. The app rewrites it for SQLAlchemy and enables SSL.

Start the API (creates the `patients` table if it is missing):

```bash
python -m app.main
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Optional sample rows (fictional data only):

```bash
python seed.py
```

## Environment

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Neon connection string |
| `VAPI_API_KEY` | Required as `X-API-Key` on the Vapi route when set |
| `API_HOST` / `API_PORT` | Bind address (default `0.0.0.0:8000`) |
| `DEBUG` | Reloads the local server when true |
| `LOG_LEVEL` | Log verbosity |

`.env` is gitignored. If `VAPI_API_KEY` is empty, the Vapi route is open for local testing.

## HTTP API

Every response is `{ "data": ..., "error": null }` or `{ "data": null, "error": { "code", "message", "details" } }`.

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/health` | Process up |
| `GET` | `/health/db` | Database ping |
| `POST` | `/api/v1/patients` | Create. Duplicate phone → `409` |
| `GET` | `/api/v1/patients` | Active patients. Filters: `last_name`, `date_of_birth`, `phone_number` |
| `GET` | `/api/v1/patients/{id}` | One active patient, else `404` |
| `PUT` | `/api/v1/patients/{id}` | Partial update |
| `DELETE` | `/api/v1/patients/{id}` | Soft delete |
| `POST` | `/api/v1/vapi/create-patient` | Voice tool. Same create logic; duplicates return `200` with `status: duplicate` |

Dates use `MM/DD/YYYY`. Phones are stored as 10 digits. Validation lives in the API, not in Vapi.

## Vapi

Tool name: `create_patient`. Call it only after the caller has heard a full read-back and confirmed. Header: `X-API-Key: {VAPI_API_KEY}`.

```
POST {API_BASE_URL}/api/v1/vapi/create-patient
```

`API_BASE_URL` is the public origin of this API. Do not hardcode it in the assistant.

**Created**

```json
{
  "data": {
    "patient_id": "UUID",
    "status": "created",
    "message": "Patient registration completed successfully."
  },
  "error": null
}
```

**Already registered**

```json
{
  "data": {
    "patient_id": "UUID",
    "status": "duplicate",
    "message": "A patient with this phone number already exists."
  },
  "error": null
}
```

Only tell the caller it worked when `status` is `created`.

### Tool schema

```json
{
  "name": "create_patient",
  "description": "Creates a patient record after the caller has confirmed every field.",
  "url": "{API_BASE_URL}/api/v1/vapi/create-patient",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "X-API-Key": "{VAPI_API_KEY}"
  },
  "parameters": {
    "type": "object",
    "properties": {
      "first_name": { "type": "string", "description": "1-50 chars. Letters, spaces, hyphens, apostrophes." },
      "last_name": { "type": "string", "description": "Same rules as first_name." },
      "date_of_birth": { "type": "string", "description": "MM/DD/YYYY, real calendar date, not in the future." },
      "sex": { "type": "string", "enum": ["Male", "Female", "Other", "Decline to Answer"] },
      "phone_number": { "type": "string", "description": "US 10-digit number. Formatting is stripped." },
      "email": { "type": "string", "description": "Optional." },
      "address_line_1": { "type": "string" },
      "address_line_2": { "type": "string", "description": "Optional." },
      "city": { "type": "string" },
      "state": { "type": "string", "description": "Two-letter US state or DC." },
      "zip_code": { "type": "string", "description": "12345 or 12345-6789." },
      "insurance_provider": { "type": "string", "description": "Optional." },
      "insurance_member_id": { "type": "string", "description": "Optional. Alphanumeric, hyphens allowed." },
      "preferred_language": { "type": "string", "description": "Optional. Defaults to English." },
      "emergency_contact_name": { "type": "string", "description": "Optional." },
      "emergency_contact_phone": { "type": "string", "description": "Optional US 10-digit number." }
    },
    "required": [
      "first_name",
      "last_name",
      "date_of_birth",
      "sex",
      "phone_number",
      "address_line_1",
      "city",
      "state",
      "zip_code"
    ]
  }
}
```

The assistant should collect fields naturally (including several in one utterance), skip what it already has, allow corrections, and never invent values. Optional fields must not block save.

## Tests

Pytest uses `DATABASE_URL` unless `TEST_DATABASE_URL` is set. It truncates `patients` between cases.

```bash
pytest -v
```

## Deploy

Host the FastAPI app anywhere that can reach Neon. Set `DATABASE_URL`, `VAPI_API_KEY`, `APP_ENV=production`, and `DEBUG=false` in that environment. Point the Vapi tool at:

```
{API_BASE_URL}/api/v1/vapi/create-patient
```
