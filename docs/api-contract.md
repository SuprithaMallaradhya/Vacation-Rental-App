# API contract

The backend uses JSON and the version prefix `/api/v1` for product routes. Operational routes remain at `/health` and `/ready`. FastAPI publishes Swagger at `/docs`, ReDoc at `/redoc`, and the generated schema at `/openapi.json`.

## Envelopes

Success: `{ "success": true, "data": ... }`

Error: `{ "success": false, "error": { "code": "...", "message": "...", "details": [] }, "request_id": "..." }`

Every response includes `X-Request-ID`; errors also include the same value in JSON. Framework validation errors use 422. Unknown routes use 404. Readiness failures use 503.

## Phase 1 operational contract

| Method | Path | Behavior |
|---|---|---|
| GET | `/health` | Process-only JSON 200; does not query PostgreSQL |
| GET | `/ready` | JSON 200 only when PostgreSQL is reachable, the Alembic revision matches the app, and required tables exist; otherwise JSON 503 |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |
| GET | `/openapi.json` | FastAPI-generated OpenAPI |

## Planned product routes

The [backend design](../BACKEND_PLAN_AND_DESIGN_V2.md) provides the shared architecture and planned features. This contract will document implemented product routes, roles, date/time rules, pagination, and analytics definitions as each phase is delivered. Initial auth/search/booking fields and errors must be reviewed by the teammate before frontend integration.

## Implemented Phase 3 authentication

| Method | Path | Access | Success |
|---|---|---|---|
| POST | `/api/v1/auth/register/customer` | Public JSON: name, email, phone, password | 201 safe user; server-assigned CUSTOMER |
| POST | `/api/v1/auth/register/host` | Same fields | 201 safe user; server-assigned HOST |
| POST | `/api/v1/auth/login` | Public JSON: email, password | 200 token_type=bearer, access_token, expires_in, expires_at, user |
| GET | `/api/v1/auth/me` | Bearer token, any authenticated role | 200 current safe user |

All success payloads are inside `data`. User fields are id/name/email/phone/role/created_at. There is no public Admin signup, and unknown request properties are rejected. Duplicate normalized email returns 409; invalid credentials or tokens return 401; wrong role returns 403; login throttle returns 429 with Retry-After. Field validation is 422 and malformed JSON is 400. No password/hash appears in user responses or validation details.

See the [authentication handoff](authentication.md) for password byte limits, token lifetime/settings, role helpers, error examples, Swagger steps, and throttle limitations, plus [JSON mock fixtures](fixtures/auth.json) for React development. Contract review and live React acceptance are still pending.

## Frontend handoff

Phase 3 is ready for the initial auth handoff. The future price field is `nightly_price`, money will serialize as decimal strings, ZIP codes remain strings, and dates use `check_in`/`check_out`. Booking state is persisted as `reservation_state=CONFIRMED|CANCELLED`; completion will be computed by the booking API. See [database conventions](database.md) for snapshot fields and the ERD. These are implementation choices for teammate review; they do not claim a completed frontend agreement.

- `[PENDING: teammate contract review]`
- `[PENDING: reachable shared API base URL; localhost alone is not a cross-machine handoff]`
- Local fake demo credentials are documented in the [authentication handoff](authentication.md).
