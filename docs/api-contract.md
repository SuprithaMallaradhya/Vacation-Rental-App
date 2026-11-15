# API contract outline

The backend uses JSON and the version prefix `/api/v1` for product routes. Operational routes remain at `/health` and `/ready`. FastAPI publishes Swagger at `/docs`, ReDoc at `/redoc`, and the generated schema at `/openapi.json`.

## Envelopes

Success: `{ "success": true, "data": ... }`

Error: `{ "success": false, "error": { "code": "...", "message": "...", "details": [] }, "request_id": "..." }`

Every response includes `X-Request-ID`; errors also include the same value in JSON. Framework validation errors use 422. Unknown routes use 404. Readiness failures use 503.

## Phase 1 operational contract

| Method | Path | Behavior |
|---|---|---|
| GET | `/health` | Process-only JSON 200; does not query PostgreSQL |
| GET | `/ready` | JSON 200 only when PostgreSQL is reachable and `alembic_version` exists; otherwise JSON 503 |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |
| GET | `/openapi.json` | FastAPI-generated OpenAPI |

## Planned product routes

The [backend design](../BACKEND_PLAN_AND_DESIGN_V2.md) provides the shared architecture and planned features. This contract will document implemented product routes, roles, date/time rules, pagination, and analytics definitions as each phase is delivered. Initial auth/search/booking fields and errors must be reviewed by the teammate before frontend integration.

## Frontend handoff

- `[PENDING: teammate contract review]`
- `[PENDING: reachable shared API base URL; localhost alone is not a cross-machine handoff]`
- `[PENDING: fake demo credentials after Phase 2 seed]`
