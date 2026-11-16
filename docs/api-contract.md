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

## Implemented Phase 5 public endpoints

- GET `/api/v1/amenities`: public reference UUID/name list.
- GET `/api/v1/listings/search`: approved-only cards with all planned filters, deterministic bounded pagination, local availability, and indicative quotes.
- GET `/api/v1/listings/{id}`: approved detail and optional stay quote.
- GET `/api/v1/listings/{id}/availability`: required stay query and quote/availability.

See [public search contract](public-search.md) for exact fields/filter semantics, date/time/DST validation, shared availability behavior, and [React mock fixtures](fixtures/search.json). Public responses exclude customer/management data. Without dates, available/total_cost/quote are null. With a valid stay, available_only defaults true; false includes valid but inventory-blocked quotes with available=false. Capacity/window/DST-invalid listings are excluded from search; singular invalid stay requests return 422. Quotes remain estimates until a future booking transaction revalidates them.

## Implemented Phase 6 Customer endpoints

| Method | Path | Success |
|---|---|---|
| POST | `/api/v1/bookings` | 201 accepted snapshots and server-calculated price |
| GET | `/api/v1/bookings/my` | 200 owned history with bounded pagination |
| GET | `/api/v1/bookings/{id}` | 200 owned saved confirmation |
| PATCH | `/api/v1/bookings/{id}/cancel` | 200 idempotent owner cancellation before accepted arrival; no body |

All four require a Customer token. Missing auth is 401, wrong role 403, foreign/missing bookings 404, occupied/unapproved booking attempts or cancellation after arrival 409, invalid stay/body fields 422. Shared nightly validation and PostgreSQL listing-first transactions protect inventory. Price, time, name/address/ZIP/timezone snapshots are retained; persisted reservation_state stays CONFIRMED/CANCELLED while response status derives COMPLETED at checkout. See [booking contract](bookings.md) and [mock JSON](fixtures/bookings.json) for exact fields, errors, concurrency behavior, and React walkthrough.

## Frontend handoff status

Phase 4 also implements the Host listing/media/hours/booking-rule/block routes and Admin listing/approval/rejection/removal/audit routes in the [management contract](listing-management.md). Host form reference amenities are at `GET /api/v1/host/amenities`; Phase 5 now also exposes public amenities and search. See [form JSON](fixtures/listings.json) for requests. Paginated lists use `success`, array `data`, and top-level `pagination`. Listing removal and rejection require JSON reasons; listing/child DELETE returns JSON 200.

Material listing/photo changes reset APPROVED to PENDING; valid nonmaterial changes preserve approval. Future/ongoing stays prevent incompatible location/timezone/capacity/window changes. New removals record actor/reason/time and retain reservations/reviews. All nested ownership is enforced server-side. UI acceptance remains pending.

Authentication, management, public search, and Customer bookings are ready for teammate contract review. The listing price field is `nightly_price`; confirmations use `nightly_price_snapshot`. Money serializes as decimal strings, ZIP codes remain strings, and dates use `check_in`/`check_out`. Booking state is persisted as `reservation_state=CONFIRMED|CANCELLED`; completion is computed by the booking API. See [database conventions](database.md) for snapshot fields and the ERD. These are implementation choices for teammate review; they do not claim a completed frontend agreement.

- `[PENDING: teammate contract review]`
- `[PENDING: reachable shared API base URL; localhost alone is not a cross-machine handoff]`
- Local fake demo credentials are documented in the [authentication handoff](authentication.md).
