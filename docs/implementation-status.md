# Implementation status

Updated: November 15, 2026

## Phase 0 — complete locally

Implemented repository guidance, design-decision logging, API contract outline, requirement coverage, backlog, and external-check register. The repository is the expected workspace on branch `backend/foundation`. No teammate frontend exists in this checkout, so no frontend files were created or changed.

### Actual checks

| Check | Result |
|---|---|
| Repository path, branch, and initial status inspected | Passed: `backend/foundation`; only the two supplied plan documents were untracked initially |
| Python/container tooling inspected | Initially Python 3.12 was unavailable. Subsequently Python 3.12.16 was installed and verified in `backend/.venv`; Docker 29.4.0 and Compose v5.1.1 are available |
| Course timezone/Demo Day | Unexecuted: instructor/course source not available; placeholder recorded |
| Team/board/instructor-sheet links | Unexecuted: values not supplied; placeholders recorded |
| Team API-contract review | Pending: teammate review is external to this checkout; contract is documented for review |

### Phase 0 checkpoint

The Phase 0 documentation commit includes `BACKEND_PLAN_AND_DESIGN_V2.md` and the project documents under `docs/`. Local assistant instructions and the local implementation plan are excluded from version control.

Commit message: `docs: add backend design, API contract, and project backlog`

## Phase 1 — foundation tests pass; database acceptance checks pending

Implemented the modular FastAPI foundation, settings, async SQLAlchemy session infrastructure, Alembic scaffold, local development/test PostgreSQL Compose services, request IDs, JSON error handling, exact development CORS origins, operational endpoints, OpenAPI, pinned dependencies, Make targets, Dockerfile, CI, and foundation tests. Schema migrations and seed data are intentionally Phase 2 work.

`/health` is process-only and does not use the database. In Phase 1, `/ready` checked connectivity and the existence of `alembic_version`; Phase 2 now also requires the expected revision and tables. The Phase 1 results below are a historical checkpoint; the Phase 2 results supersede the earlier runtime limitations.

### Checks to run / results in this environment

| Check | Result |
|---|---|
| Setup | User reported setup worked; `backend/.venv/bin/python --version` confirms Python 3.12.16. Setup was not rerun during commit review |
| `make db-up` | Earlier attempt failed because Docker Desktop's daemon was unavailable. Successful database startup has not been independently verified |
| `make api` and live `/health` | Live Uvicorn startup was not rechecked during commit review; `/health` JSON 200 passes through TestClient |
| `/ready` unavailable-dependency behavior | Foundation test verifies JSON 503 in the current environment; controlled database stop/restart remains unexecuted |
| `/docs`, `/redoc`, `/openapi.json` | Passed through TestClient, including schema route checks; browser verification unexecuted |
| Database isolation | Configuration checks pass; separate running PostgreSQL instances and data isolation remain unverified |
| `make verify` | Passed on Python 3.12.16: Ruff lint and all 5 foundation tests; 1 upstream Starlette/AnyIO deprecation warning |
| `git diff --check` | Passed during commit review |
| `docker compose config --quiet` | Passed in the initial Phase 1 review |
| CI definition | Added; GitHub execution pending push |

The verification command expands to `backend/.venv/bin/python -m ruff check backend` and, from `backend/`, `.venv/bin/python -m pytest tests` with `TEST_DATABASE_URL=postgresql+asyncpg://vacation:vacation@localhost:5433/vacation_rental_test` supplied by the Makefile. The earlier Python 3.11 compatibility run also passed, but the current result uses the required Python 3.12 runtime.

### Phase 1 checkpoint

The foundation commit includes `backend/`, `compose.yaml`, `Makefile`, `.github/workflows/ci.yml`, `.gitignore`, and `README.md`. Only the environment example is included; local environment values, virtual environments, generated metadata, and caches are ignored.

Commit message: `feat: add FastAPI foundation with PostgreSQL setup and tests`

No cloud resources, paid services, secrets, or external API keys were used.

## Phase 2 — implemented and locally verified

Implemented all 11 domain tables, UUID/FK/unique/check constraints, Decimal money and immutable-history snapshot fields, weekly contact hours and booking rules, moderation records, indexes, and a frozen Alembic migration. The migration installs `btree_gist` and a partial GiST exclusion constraint preventing overlapping confirmed nightly bookings. Booking APIs, listing row locks, and service-level role/ownership/date validation remain their planned later phases.

Added development-only deterministic seed data: 6 users (1 Admin/2 Hosts/3 Customers), 12 listings, 6 amenities, 45 amenity links, 84 contact-hour rows, 84 booking-rule rows, 12 photos, 12 blocks, 10 moderation records, 18 bookings, and 7 eligible reviews. Fixtures include all listing states, four ZIP codes including `02108`, historical/future/cancelled stays, and exact 30/60/90-day creation boundaries with adjacent microseconds. Reruns preserve existing rows and edits.

Added a source ERD and readable SVG export, database documentation, stricter test/seed target guards, schema-aware readiness, and real PostgreSQL tests. Test application settings are redirected to the validated test URL before importing the engine. Each database test migrates a fresh UUID schema and removes only that schema afterward.

### Local port correction

The first development migration connection reached an existing native PostgreSQL listener on 5432 and failed with `role "vacation" does not exist`. The project containers now bind to `127.0.0.1:55432` and `127.0.0.1:55433`. Defaults, examples, Make targets, CI, and README are updated. Existing Docker volumes were preserved; the native database was not modified. Existing local `.env` files must use the new ports.

### Actual commands and results

| Command/check | Result |
|---|---|
| `backend/.venv/bin/python -m pip install -e 'backend[dev]'` | Passed with network permission after sandbox DNS blocked the first attempt; bcrypt 5.0.0 installed |
| `make db-up` | Passed; both named PostgreSQL containers healthy on the new loopback ports |
| `make migrate` | Passed: upgrade from zero to `0001_initial_schema` |
| `make seed` | Passed with the row counts above |
| `make seed` again | Passed: zero inserts in every table, no updates/deletes |
| `make test TEST_PATH=tests/database` | Passed: 28 real PostgreSQL tests, including fresh migration, downgrade/upgrade, invalid FK/duplicates/prices/dates/ratings/windows/media/reasons, rollback, history/types/indexes, seed preservation, and concurrent overlap |
| `make verify` | Passed: Ruff, all 41 tests on Python 3.12.16, and Alembic check reporting `No new upgrade operations detected`; 1 upstream Starlette/AnyIO deprecation warning |
| `backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8011` | Passed startup; temporary server stopped after checks |
| Live HTTP checks on port 8011 using Python `urllib.request` | `/health`, `/ready`, `/docs`, `/redoc`, `/openapi.json`: 200; unknown `/missing`: JSON 404; request IDs verified |
| `docker compose stop postgres-dev`, then live HTTP checks | Passed: `/health` stays JSON 200, `/ready` becomes JSON 503 with matching request ID |
| `docker compose up -d --wait postgres-dev`, then live readiness | Passed: `/ready` recovers to 200 |
| Development identity/count query below | Confirmed dev identity and unchanged counts: 6 users, 12 listings, 18 bookings, 7 reviews |
| Test identity/catalog query below | Confirmed `vacation_rental_test`, zero public application tables, zero leftover `test_%` schemas |
| `git diff --check`; SVG parsed with Python ElementTree | Passed whitespace and SVG XML checks |

Exact read-only database verification commands:

```bash
docker compose exec -T postgres-dev psql -U vacation -d vacation_rental_dev -Atc "SELECT current_database(), (SELECT count(*) FROM users), (SELECT count(*) FROM listings), (SELECT count(*) FROM bookings), (SELECT count(*) FROM reviews)"
docker compose exec -T postgres-test psql -U vacation -d vacation_rental_test -Atc "SELECT current_database(), (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'), (SELECT count(*) FROM information_schema.schemata WHERE schema_name LIKE 'test_%')"
```

Sandboxed database tests initially failed because local TCP access was denied; they passed with local-network permission. The initial Alembic logging placeholder also lacked logger `qualname` entries; these were fixed before migration. These failures are resolved and are not claimed as successful first attempts.

### Remaining checks and boundaries

- GitHub CI execution for this change is pending push; local CI-equivalent lint/tests pass.
- Frontend integration, teammate contract approval, course timezone/Demo Day, team links, and live Google Maps remain pending.
- No cloud resources or paid services were used. Future Azure preflight must verify `btree_gist` allowlisting/installation permissions.
- Only test-generated UUID schemas were removed; no database, development data, or volume was deleted. Test schemas contain disposable fixtures and are recreated by the suite.
- Phase 2 checkpoint commit: `feat: add rental schema, migrations, and repeatable demo seed`. Git history records the final commit identifier; GitHub CI results are tracked separately after push.

## Next phase

Phase 3 will implement Customer/Host registration, JSON login for all three roles, bcrypt verification, expiring JWTs, `/auth/me`, role/ownership dependencies, login throttling, and the auth frontend contract. It has not started.
