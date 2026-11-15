# Vacation Rental App

The backend is in `backend/`. The React frontend is owned by the teammate. Phases 0–2 provide the foundation, database schema, and demo data; authentication and product APIs are still planned.

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

Local demo accounts: `admin@example.test`, `host1@example.test`, `host2@example.test`, and `customer1@example.test` through `customer3@example.test`. All use the deliberately public demo password `DemoOnly!2026`, stored only as bcrypt hashes in the database. Login endpoints arrive in Phase 3.

The seed CLI refuses cloud/test/production targets and only permits `APP_ENV=development` with the local `vacation_rental_dev` database. The seed uses an anchored timeline; reruns preserve user edits and existing dates. To obtain a newer timeline later, use a separately approved local data-refresh procedure rather than silently resetting data.

## Project documents

- [Implementation status](docs/implementation-status.md)
- [Design decisions](docs/design-decisions.md)
- [API contract](docs/api-contract.md)
- [Requirement coverage](docs/requirement-coverage.md)
- [Product backlog](docs/product-backlog.md)
- [External checks](docs/external-checks.md)
- [Backend design V2](BACKEND_PLAN_AND_DESIGN_V2.md)
- [Database schema and ERD](docs/database.md)
