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

## Phase 3 — implemented and locally verified

Branch: `backend/auth`, created from `origin/main` at `f389ed3` after the Phase 2 pull request was merged. Local feature branch tracking was cleared so it will not accidentally use `origin/main` as its push target. No teammate changes were present at the start.

Implemented JSON Customer/Host signup, JSON login for Customer/Host/seeded Admin, authenticated `/api/v1/auth/me`, bcrypt hashing/verification in worker threads, validated expiring JWTs, current database role checks, and reusable role/ownership helpers. Signup rejects role/property injection and handles concurrent duplicate normalized email atomically. No schema migration was needed.

Added safe user response models, generic invalid credentials, a bounded process-local login throttle with Retry-After, Swagger HTTP bearer authentication, OpenAPI examples, and React mock JSON fixtures. Local startup disables proxy-header trust. Password/hash values are excluded from responses and validation details; unexpected error logs record only exception class/request ID, and database exceptions hide SQL parameters. JWT signing defaults to a random local process key; explicit strong configuration is required outside development/test.

### Files changed

- New backend modules: `core/security.py`, `core/dependencies.py`, `core/errors.py`, `core/throttle.py`, `routers/auth.py`, `schemas/auth.py`, `schemas/common.py`, and `services/auth.py`, with package initializers.
- Updated settings/environment example, application factory/router wiring, exception handling, database logging configuration, dependency pins, and Make/Docker startup.
- New auth tests and shared PostgreSQL fixtures at `backend/tests/fixtures/database.py` (moved from the database-only conftest); database tests now import that shared helper.
- Updated README, API contract, design decisions, requirement coverage, this status report, and added `docs/authentication.md` plus `docs/fixtures/auth.json`.

### Actual commands and results

| Command/check | Result |
|---|---|
| `git fetch origin main`; `git switch -c backend/auth origin/main` | Passed; main includes Phase 2 merge `f389ed3`. Branch upstream was then unset |
| `backend/.venv/bin/python -m pip install -e 'backend[dev]'` | Passed: pinned PyJWT 2.15.1 and email-validator 2.4.0 installed; official package docs consulted |
| `make test TEST_PATH=tests/auth/test_security.py` | Initial targeted run passed: 23 unit/security tests |
| `make test TEST_PATH=tests/auth` | Initial targeted run passed: 61 tests. Two additional fixture/log-safety checks were then added and passed in the full suite |
| `make verify` | Passed: Ruff, all 104 tests on Python 3.12.16 (63 auth + 28 database + 13 foundation), and Alembic drift check reporting no new upgrade operations |
| `backend/.venv/bin/ruff format --check backend`; `git diff --check` | Passed |
| `make openapi` | Passed; exported schema has four auth endpoints, JSON login, documented errors, and HTTP bearer security; export remains ignored |
| `backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8011 --no-proxy-headers` | Passed temporary live startup; server stopped after smoke checks |
| Live HTTP checks via Python urllib | Customer, Host, and Admin JSON login each returned 200, and their bearer `/auth/me` returned the same safe user. Readiness remained 200 |
| Live invalid-auth checks | Missing bearer: JSON 401 with WWW-Authenticate; wrong password: generic JSON 401; Admin role injection at Customer signup: JSON 422, without creating a user |

Initial formatting/type-parameter lint findings were corrected before the full gate. The final suite has one existing upstream Starlette/AnyIO deprecation warning; no failed tests or migration drift remain. Registration, role gates, token tampering/expiry, throttling, safe logs, and duplicate races are exercised against the isolated real PostgreSQL test setup. Demo users were not changed by the live smoke checks.

### Frontend handoff and boundaries

- Backend auth is ready for teammate review. [Authentication handoff](authentication.md) describes the base URL/setup, Swagger authorization, fake demo credentials, expiry/401/403 handling, and public mock fixtures.
- Actual React login and one authenticated request remain pending teammate integration. Swagger's HTTP bearer contract is tested and real bearer requests work; manually clicking the Swagger Authorize UI in a browser was not performed.
- The login limiter is process-local, not distributed. Shared/edge throttling, proxy trust, HTTPS, and a shared signing secret must be verified before multi-VM deployment. No cloud resources or paid services were introduced.
- No refresh/logout endpoint or password-reset flow was added. Tokens remain valid until expiry while the user exists; React logout clears its in-memory token.
- Course timezone/Demo Day, team/board/instructor links, and actual frontend contract approval remain pending.
- Phase 3 checkpoint commit: `feat: add JSON authentication, JWTs, and role enforcement`. Git history records the final commit identifier; GitHub CI results are tracked separately after push.

## Phase 4 — implemented and locally verified

Branch: `backend/listings-moderation`, created without upstream tracking from merged `origin/main` at `670953f` (Phase 3 merge). The working tree was clean before implementation.

Implemented all 20 planned Host/Admin operations plus protected Host amenity references (21 operations total): Host listing create/list/detail/patch/soft-remove, weekly contact hours and booking rules, media add/patch/delete, date-block list/add/delete, and Admin list/pending/detail/approve/reject/remove/audit history. APIs use bearer roles, scoped nested ownership, request/response models, decimal money strings, numeric coordinates, bounded deterministic pagination, and JSON deletes.

Added pending/approved/rejected/removed transitions, complete approval validation with field details, material-edit reapproval, atomic moderation audit rows, and one listing-first row-lock helper for all mutations. Blocks reject overlapping noncancelled reservations and other blocks. Future/ongoing stays protect location/timezone, accepted UTC booking windows, and guest capacity. Removal is terminal/idempotent and preserves bookings/reviews; Host/Admin removals require a reason.

### Additive audit schema decision

The existing `admin_actions` table has an Admin-specific actor, so Host removals must not be written there. Added `listing_removals` with unique listing FK, actual user actor FK, nonblank reason, and UTC timestamp through `0002_listing_removal_audit`. Admin removal inserts both records in the same transaction. The migration preserves all existing rows and does not invent missing legacy metadata. The guarded seed adds only the known fake removal record. Readiness now requires the new head/table, and the ERD documents all 12 current tables.

### Files changed

- New: `backend/app/routers/host.py`, `routers/admin.py`, `schemas/listings.py`, `services/listings.py`, and `backend/alembic/versions/0002_listing_removal_audit.py`.
- Updated: listing-removal model exports, schema readiness, demo seed, app router wiring, shared pagination/structured errors.
- New: `backend/tests/listings/` lifecycle, role/ownership, validation, rollback, history, concurrency, and OpenAPI tests.
- Updated/new handoff: README, API contract, database/decision/coverage/status docs, `docs/listing-management.md`, `docs/fixtures/listings.json`, and ERD source/export.

### Actual commands and results

| Command/check | Result |
|---|---|
| `git fetch origin main`; `git switch --no-track -c backend/listings-moderation origin/main` | Passed; Phase 3 merge `670953f` confirmed before branch creation |
| `make migrate` | Passed additive upgrade from `0001_initial_schema` to `0002_listing_removal_audit` |
| `make seed` | Existing development dataset retained; inserted exactly 1 fake listing_removals row and 0 in every existing table |
| `make seed` again | Passed: 0 inserts in every table |
| `make test TEST_PATH=tests/listings/test_validation.py` | Passed: 50 validation/rollback/OpenAPI cases |
| `make test TEST_PATH=tests/listings` | Passed: 68 Phase 4 tests; real PostgreSQL used for API/constraint/transaction tests |
| `make verify` | Passed: Ruff, all 172 backend tests on Python 3.12.16, Alembic drift check with no new upgrade operations; 1 existing Starlette/AnyIO deprecation warning |
| `backend/.venv/bin/ruff format --check backend`; `git diff --check` | Passed |
| `make openapi` | Passed; 21 new protected Host/Admin operations, typed schemas and errors exported; export remains ignored |
| Final Swagger form example validation and targeted OpenAPI test | Passed: seven-day hours/rules, media, block, and reason examples validate against request models; OpenAPI regression test passed after example metadata was added |
| Request fixtures validated against Pydantic models; Markdown links and ERD SVG XML parsed | Passed for all listing form examples and local documentation links |
| Temporary Uvicorn with `--app-dir backend --host 127.0.0.1 --port 8011 --no-proxy-headers` | Passed startup; stopped after live smoke checks |
| Live Host/Admin reads via urllib | Own paginated listing/detail/amenities, Admin pending/detail/audit, `/ready`, and `/openapi.json` returned 200; money strings/numeric coordinates verified |
| Live role/ownership/injection checks | Host B reading Host A: 404; Customer on Host route and Host on Admin route: 403; client status injection: JSON 422 with no listing update |
| Read-only development identity/count query | `vacation_rental_dev`, revision `0002_listing_removal_audit`, 7 users, 12 listings, 18 bookings, 7 reviews, 1 removal record. The seventh user was preexisting and was preserved |
| Read-only test identity/catalog query | `vacation_rental_test`, 0 public application tables, 0 leftover temporary test schemas |

The first management-only run passed 18 tests; the additional validation/rollback cases then passed, followed by the 68-test Phase 4 gate and complete 172-test regression. Formatting findings were resolved before final gates. No failed or blocked automated check remains.

### Handoff and boundaries

- Backend management/moderation is ready for teammate review with [route/field/state documentation](listing-management.md) and [form fixtures](fixtures/listings.json).
- Host → Admin → Customer UI integration and manual browser clicks remain unexecuted. The HTTP lifecycle is tested on real isolated PostgreSQL; public Customer search arrives in Phase 5.
- Listing-first locks are implemented and tested for Phase 4 writers. Booking/cancellation creation and booking-versus-block/moderation races remain Phase 6, using the same lock order.
- No frontend files, cloud resources, paid services, or unrelated user data were changed. Only generated disposable test schemas were removed by fixture cleanup; databases/volumes and development data were preserved.
- Existing removals with unknown actors/reasons may retain `removal=null`; the migration deliberately avoids fabricated history.
- Course timezone/Demo Day, team/board/instructor links, and actual teammate contract approval remain pending.
- Phase 4 checkpoint commit: `feat: add Host listing management and Admin moderation`. Git history records the final commit identifier; GitHub CI results are tracked separately after push.

## Next phase

Phase 5 will implement public approved-listing search, details, amenities, availability, and server quotes, including nightly date/time validation, guest/city/state/ZIP/radius filters, pagination, and shared availability logic for Phase 6 bookings. It has not started.
