# Vacation Rental App

The backend is in `backend/`. The React frontend is owned by the teammate. Phases 0–8 provide the foundation, schema/demo data, authentication, Host management, Admin moderation, public search/details/availability/quotes, Customer bookings/history/cancellation, reviews/ratings, and Host/Admin analytics. Shared React/Google Maps integration and production/deployment work remain planned.

## Prerequisites

- Python 3.12 (required; `make setup` checks this)
- Docker Desktop or another Docker-compatible runtime with Compose
- GNU Make

## Local setup

```bash
cp backend/.env.example backend/.env
make setup
make db-up
make migrate
make seed
```

`make migrate` applies Alembic migrations. `make seed` inserts missing demo rows without updating or deleting existing data; a second run reports zero inserts. Neither command runs automatically at API startup.

If you already have a local `.env` from Phase 1, update its two database URLs to match the new ports in `backend/.env.example`. Ports 55432 and 55433 avoid conflicts with an existing PostgreSQL installation on 5432. The database services bind only to `127.0.0.1`.

## Run the API

```bash
make api
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/ready
open http://127.0.0.1:8000/docs
```

`/health` is process-only and returns JSON 200 even when PostgreSQL is unavailable. `/ready` returns JSON 200 when PostgreSQL is reachable, all required tables exist, and its migration revision matches the application. It returns JSON 503 before migrations, for a stale schema, or during a database outage. Swagger, ReDoc, and OpenAPI are at `/docs`, `/redoc`, and `/openapi.json`.

## Verification

```bash
make test TEST_PATH=tests/foundation
make test TEST_PATH=tests/auth
make test TEST_PATH=tests/listings
make test TEST_PATH=tests/search
make test TEST_PATH=tests/bookings
make test TEST_PATH=tests/reviews
make test TEST_PATH=tests/analytics
make test
make lint
make schema-check
make openapi
make verify
make db-down
```

`make verify` runs lint, all tests, and model/migration drift checks. Both database services must be running and the development database must be migrated. CI runs lint and tests with a separate PostgreSQL service; it does not deploy anything.

| Purpose | Address | Database |
|---|---|---|
| Development | `127.0.0.1:55432` | `vacation_rental_dev` |
| Tests | `127.0.0.1:55433` | `vacation_rental_test` |

Tests require a local `TEST_DATABASE_URL` naming a separate database ending in `_test`. The test harness assigns the application to that URL before importing its engine. Each database test migrates a fresh `test_<uuid>` schema and removes only that schema afterward. It does not truncate development tables, reset databases, or delete volumes. A failed test connection fails the suite instead of silently skipping database tests.

`make db-down` stops the containers and preserves both volumes. No reset or volume deletion runs during setup, migrations, seed, or tests.

## Demo data

The dataset contains 1 Admin, 2 Hosts, 3 Customers, 12 listings across 4 ZIP codes, 18 bookings, and 7 eligible past-stay reviews. It also contains all listing states, varied prices/capacities, weekly hours/windows, photos, amenities, date blocks, cancellations, and moderation records. Booking creation timestamps cover the exact 30/60/90-day analytics boundaries and one microsecond on each side, relative to the initial seed time.

Local demo accounts: `admin@example.test`, `host1@example.test`, `host2@example.test`, and `customer1@example.test` through `customer3@example.test`. All use the deliberately public demo password `DemoOnly!2026`, stored only as bcrypt hashes in the database. These accounts can now log in through `POST /api/v1/auth/login` using JSON.

The seed CLI refuses cloud/test/production targets and only permits `APP_ENV=development` with the local `vacation_rental_dev` database. The seed uses an anchored timeline; reruns preserve user edits and existing dates. To obtain a newer timeline later, use a separately approved local data-refresh procedure rather than silently resetting data.

## Authentication

Use `/api/v1/auth/register/customer` or `/api/v1/auth/register/host` with name, email, phone, and password. Roles are assigned by the server; Admin signup is not public. Login uses JSON email/password and returns an access token plus the safe user record inside `data`. In Swagger, submit the login example, click **Authorize**, paste `data.access_token`, then call `/api/v1/auth/me`.

Access tokens expire after 60 minutes by default. A blank `JWT_SECRET_KEY` generates a random process key in development/test, so restart/reload invalidates tokens. To keep local tokens across restarts, generate a secret and store it only in the ignored `.env`; an explicit secret of at least 32 bytes is mandatory outside development/test. Do not reuse the older example placeholder.

The basic process-local login limit is 10 attempts per client IP per 60 seconds. Login may return 429 with Retry-After; it is not a distributed limit across future VMs. See the [auth contract and React handoff](docs/authentication.md) for exact request/response examples, validation, 401/403 handling, and deployment limitations.

## Host listings and Admin moderation

After updating, run `make migrate` and `make seed`. Revision `0002_listing_removal_audit` adds removal history without changing existing listings/bookings. Hosts can create/edit their own pending listings, maintain media/amenities/contact hours/booking rules/date blocks, and soft-remove listings with a reason. Admins can review pending listings, approve/reject them, remove them with an audit record, and view moderation history.

Use the Host/Admin groups in Swagger with the appropriate demo token. Start with `GET /api/v1/host/amenities` for reference IDs. Complete listing details, a photo, and all seven weekdays of hours/rules before approval. Material edits require reapproval; future accepted stays protect their location, capacity, and booking windows. All DELETE endpoints return JSON, and listing removal requires a JSON reason. Read the [listing management contract](docs/listing-management.md) and [form examples](docs/fixtures/listings.json) before connecting React.

## Public search

Public endpoints now include `/api/v1/amenities`, `/api/v1/listings/search`, `/api/v1/listings/{id}`, and `/api/v1/listings/{id}/availability`. Browse without dates returns null quote/availability. Supply check_in plus check_out or duration_nights for 1–14-night quotes. Only approved listings are public; quotes do not reserve inventory. See the [public search contract](docs/public-search.md) for filters, timezone/DST rules, mock fixtures, and frontend integration. Existing checkouts should run `make setup` to install the timezone-data fallback dependency; no new migration is required.

## Customer bookings

Log in as a Customer and use the **customer bookings** Swagger group. POST `/api/v1/bookings` accepts a listing ID and the selected stay, calculates the current total on the server, and reserves available nights in a transaction. GET `/api/v1/bookings/my` lists your saved history; GET `/api/v1/bookings/{id}` shows your confirmation. PATCH `/api/v1/bookings/{id}/cancel` takes no body and cancels your future stay before arrival. Repeated cancellation preserves the original result. Details/prices survive listing edits/removal; completion is computed after checkout. See the [walkthrough and contract](docs/bookings.md) and [JSON examples](docs/fixtures/bookings.json). Phase 6 requires no new migration or dependency.

## Reviews and ratings

Customers can POST `/api/v1/reviews` with an owned noncancelled checked-out booking ID, integer rating 1–5, and a comment. Each booking can be reviewed once. GET `/api/v1/listings/{id}/reviews` publicly lists eligible reviews for an approved listing; search/detail rating aggregates update from the same eligibility rules. The original seed's eligible completed stays already have reviews, so duplicate rejection is expected for those IDs. See the [review walkthrough](docs/reviews.md), [JSON examples](docs/fixtures/reviews.json), and [phase audit](docs/phase-acceptance.md). No new migration or dependency is required.

## Host and Admin analytics

Use GET `/api/v1/host/analytics` with a Host token or GET `/api/v1/admin/analytics` with an Admin token. Both accept period_days=30/60/90 (default 30) and optional zip_code, and return current inventory/status counts, new listings, booking/cancellation/net counts, saved booking value, ZIP breakdowns, and UTC daily buckets. Host scope comes from auth. Booking value uses saved noncancelled totals and is not paid revenue. ZIPs use current listings versus saved booking ZIPs. See the [analytics walkthrough and metric/chart definitions](docs/analytics.md) and [JSON examples](docs/fixtures/analytics.json). No new migration or dependency is required.

## Project documents

- [Implementation status](docs/implementation-status.md)
- [Design decisions](docs/design-decisions.md)
- [API contract](docs/api-contract.md)
- [Authentication and frontend handoff](docs/authentication.md)
- [Host listings and Admin moderation](docs/listing-management.md)
- [Public search, availability, and quotes](docs/public-search.md)
- [Customer bookings, history, and cancellation](docs/bookings.md)
- [Reviews and ratings](docs/reviews.md)
- [Host and Admin analytics](docs/analytics.md)
- [Backend phase acceptance audit](docs/phase-acceptance.md)
- [Requirement coverage](docs/requirement-coverage.md)
- [Product backlog](docs/product-backlog.md)
- [External checks](docs/external-checks.md)
- [Backend design V2](BACKEND_PLAN_AND_DESIGN_V2.md)
- [Database schema and ERD](docs/database.md)
