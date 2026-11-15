# Vacation Rental App

Backend foundation is in `backend/`; the React frontend remains teammate-owned and is not duplicated here.

## Prerequisites

- Python 3.12 (required; `make setup` checks this)
- Docker Desktop or another Docker-compatible runtime with Compose
- GNU Make

## Local setup

```bash
cp backend/.env.example backend/.env
make setup
make db-up
```

Phase 1 does not include the schema migration or seed data. `make migrate` and `make seed` intentionally stop with a Phase 2 message. Consequently, `/ready` is expected to return JSON 503 until Phase 2 creates `alembic_version`.

## Run the API

```bash
make api
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/ready
open http://127.0.0.1:8000/docs
```

`/health` is process-only and returns JSON 200 even when PostgreSQL is unavailable. `/ready` checks PostgreSQL and schema readiness and returns JSON 503 when either dependency is unavailable. Swagger, ReDoc, and OpenAPI are at `/docs`, `/redoc`, and `/openapi.json`.

## Verification

```bash
make test TEST_PATH=tests/foundation
make test
make lint
make openapi
make verify
make db-down
```

The Compose file starts isolated databases: development on `localhost:5432` (`vacation_rental_dev`) and test on `localhost:5433` (`vacation_rental_test`). Tests require the separate `TEST_DATABASE_URL` and never default to the development database.

## Project documents

- [Implementation status](docs/implementation-status.md)
- [Design decisions](docs/design-decisions.md)
- [API contract](docs/api-contract.md)
- [Requirement coverage](docs/requirement-coverage.md)
- [Product backlog](docs/product-backlog.md)
- [External checks](docs/external-checks.md)
- [Backend design V2](BACKEND_PLAN_AND_DESIGN_V2.md)
