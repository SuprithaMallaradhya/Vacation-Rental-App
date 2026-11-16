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

## Phase 5 — implemented and locally verified

Branch: `backend/search-availability`, created without upstream tracking from merged `origin/main` at `51054b2` (Phase 4 merge). The working tree was clean before implementation.

Implemented four public GET endpoints: amenities, approved listing search, approved detail, and single-listing availability. Search combines dates/duration/local times, guests, city/state/text ZIP, coordinates/radius, amenity UUIDs, price bounds, availability, sort, and bounded pagination with AND semantics. Cards/detail include media, amenities, coordinates, cost rating, eligible review aggregates, listing-local bookings_today, and indicative quotes; detail adds contact fields/hours and booking windows. Pending/rejected/removed records and private management/customer data remain hidden.

Added shared stay resolution and half-open inventory helpers for 1–14 local nights, strictly future arrival, weekday windows/defaults, capacity, DST ambiguity/gaps, Decimal totals, confirmed reservations, and date blocks. Browsing returns null quote/availability. Dated search defaults available_only=true; false includes inventory conflicts with available=false and an indicative quote, while invalid local stays are still excluded. Quotes reserve nothing; Phase 6 must revalidate under the listing lock.

### Files changed

- Added `backend/app/core/clock.py`, `routers/listings.py`, `schemas/search.py`, `services/availability.py`, and `services/search.py`; updated router wiring in `app/main.py`.
- Added `backend/tests/search/` fixtures and 72 validation, API, display, privacy, timezone, inventory, filter, pagination, and OpenAPI tests.
- Updated `backend/pyproject.toml` with pinned `tzdata==2026.6` as the fallback for systems without IANA timezone data. No schema/model/migration change; head remains `0002_listing_removal_audit`.
- Added `docs/public-search.md` and `docs/fixtures/search.json`; updated README, API contract, decisions, requirement coverage, and this status document.

### Actual commands and results

| Command/check | Result |
|---|---|
| `git fetch origin main`; `git switch --no-track -c backend/search-availability origin/main` | Passed; verified Phase 4 merge `51054b2` before branch creation |
| `backend/.venv/bin/python -m pip install -e 'backend[dev]'` | Passed; installed the pinned timezone-data dependency in the existing Python 3.12 environment |
| `make test TEST_PATH=tests/search/test_validation.py` | Initial 44-case unit run passed; added boundary case is included in the final 72-test suite |
| `make test TEST_PATH=tests/search/test_search.py` | Passed: 22 real-PostgreSQL API/filter/privacy/OpenAPI tests |
| `make test TEST_PATH=tests/search/test_display.py` | Passed: 5 rating/cost/timezone/pagination/radius tests |
| `make test TEST_PATH=tests/search` | Passed: all 72 Phase 5 tests |
| `make verify` | Passed: Ruff, all 244 backend tests on Python 3.12.16, and Alembic drift check (no new upgrade operations). One existing Starlette/AnyIO deprecation warning |
| `make openapi` | Passed; four public operations exported without an auth requirement; generated export remains ignored |
| Search JSON request/response/error examples validated against Pydantic models | Passed |
| Temporary `backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8011 --no-proxy-headers` | Passed startup and shutdown after read-only HTTP checks |
| Live urllib GET checks | Health/readiness/OpenAPI/amenities/search/detail/availability: 200. Browse nulls, matching quotes, numeric coordinates, decimal money, 14-night stay and combined city/state/ZIP/radius filters passed. 15-night stay and availability-only browse: standard JSON 422 with matching request IDs |
| Read-only development identity/count SQL | `vacation_rental_dev`, revision `0002_listing_removal_audit`, 7 users, 12 listings, 18 bookings, 7 reviews, 1 removal; existing demo data preserved |
| Read-only test catalog SQL | `vacation_rental_test`, 0 public tables, 0 leftover temporary test schemas |
| `backend/.venv/bin/ruff format --check backend`; final `make lint`; `git diff --check` | Passed: 64 Python files formatted, no lint or whitespace findings |
| Final review of all 20 changed/new files | Local Markdown links and JSON parsed; common secret-signature scan found no matches. No frontend/ignored private files included; Git index remains empty |

An early command mistakenly passed pytest's `-x` flag to make, which rejected the invocation before running tests. It was corrected; all final automated gates passed. No failed or blocked automated check remains. Live React login → search → detail and manual browser acceptance remain unexecuted pending teammate integration. GitHub CI has not run for these unpushed changes.

### Review and handoff

The [public API guide](public-search.md) and [mock fixtures](fixtures/search.json) are ready for teammate review. Search uses coarse SQL filtering and bulk reads followed by local eligibility/radius/pagination for the small demo catalog; production-scale spatial pagination is outside this phase. No Google key, frontend change, Azure provisioning, paid service, or development data mutation was needed. Course timezone/Demo Day, team links, and shared API acceptance remain pending external confirmations.

Phase 5 was initially handed off unstaged, uncommitted, and unpushed. The user subsequently authorized committing and pushing this phase on `backend/search-availability`. Checkpoint message: `feat: add public listing search, availability, and quotes`. Git history records the final commit identifier; GitHub CI results are tracked separately after push.

## Phase 6 — implemented and locally verified

Branch: `backend/bookings-cancellation`, created without upstream tracking from merged `origin/main` at `21ed13a` (Phase 5 merge). Confirmed `f856ae1` is an ancestor of main; the working tree was clean before implementation. The implementation was initially handed off without a commit or push.

Implemented Customer POST booking creation, GET owned history, GET saved confirmation, and PATCH cancellation. Creation reuses the Phase 5 stay/inventory validator after acquiring the existing listing lock, rechecks approval/windows/capacity/price and current time, calculates Decimal totals on the server, and atomically persists accepted price/name/address/ZIP/timezone/UTC snapshots. Customer identity comes from auth; price/state/owner injection is rejected. Booking history retains removed-listing confirmations and uses deterministic bounded pagination, including safe empty responses for very large out-of-range page numbers.

Cancellation locks listing before booking, verifies ownership, allows cancellation strictly before accepted arrival, preserves repeated cancellation state/timestamps, and releases nightly inventory. Removed listings can still have their valid future owned booking cancelled. Failures roll back; the named PostgreSQL exclusion violation becomes a safe 409. CONFIRMED/CANCELLED remain persisted states; COMPLETED and can_cancel are computed from accepted UTC timestamps without a scheduler. A clock callable is read after waiting for a lock so arrival/cancellation checks do not use stale request-start time.

### Files changed

- Added `backend/app/routers/bookings.py`, `schemas/bookings.py`, and `services/bookings.py`; updated `core/clock.py` and app router wiring.
- Added `backend/tests/bookings/`: isolated API/clock fixtures, helpers, lifecycle/authorization/validation, transaction rollback, and real concurrency tests (72 cases total; 15 concurrency cases).
- Added `docs/bookings.md` and `docs/fixtures/bookings.json`; updated README, API contract, public search guide, decisions, coverage, and this status report.
- No model, migration, dependency, CI configuration, or environment change was needed. Existing CI discovers all new tests; current Alembic head remains `0002_listing_removal_audit`.

### Actual commands and results

| Command/check | Result |
|---|---|
| `git fetch origin`; `git merge-base --is-ancestor f856ae1 origin/main`; `git switch --no-track -c backend/bookings-cancellation origin/main` | Passed; merged Phase 5 confirmed at main `21ed13a`, fresh branch created |
| Initial `make test TEST_PATH=tests/bookings` | 52 passed, 2 failed (54 initial tests): equal frozen create/cancel timestamps let ORM onupdate expire updated_at, triggering implicit async loading during confirmation serialization |
| Cancellation fix and expanded booking gate | Replaced cancellation write with explicit UPDATE RETURNING; all 68 then-current cases passed, including real lock-wait races |
| `make test TEST_PATH=tests/bookings` after added rollback/window cases | Passed: all 72 booking tests |
| `make verify` | Passed: Ruff, all 316 backend tests on Python 3.12.16, and Alembic drift check with no new upgrade operations; one existing Starlette/AnyIO deprecation warning |
| Final `make verify` after very-large-page regression fix | Passed again: all 316 tests, Ruff, and no migration drift; one existing deprecation warning |
| `backend/.venv/bin/ruff format --check backend`; `git diff --check` | Passed: 74 Python files formatted, no whitespace errors |
| `make openapi` | Passed; all four booking operations exported with BearerAuth, request/response/error schemas and request example; export remains ignored |
| Booking fixture and Swagger example validation against Pydantic models | Passed: create, confirmation, cancellation, empty history, error fixtures; accepted snapshots unchanged by cancellation |
| Final project-file review | All 20 changed/new files checked; local Markdown links and JSON parsed, common secret-signature scan had no matches. Frontend/private ignored files excluded; Git index remains empty |
| Temporary `backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8011 --no-proxy-headers` | Passed startup and shutdown after smoke checks |
| Live urllib checks | Health/readiness/Swagger/ReDoc/OpenAPI, Customer login and owned history/detail: 200. Missing auth: JSON 401; malformed booking UUID: JSON 422; request IDs/money strings/history consistency verified. No development booking writes performed |
| `docker compose ps`; read-only development identity/count SQL | Both databases healthy. `vacation_rental_dev`, revision `0002_listing_removal_audit`, 7 users, 12 listings, 18 bookings, 7 reviews, 1 removal; existing development data preserved |
| Final read-only test identity/catalog SQL | `vacation_rental_test`, 0 public tables, 0 leftover temporary test schemas |

Concurrency tests use independent sessions/connections and observe PostgreSQL `pg_blocking_pids`, rather than assuming a delay means contention. They prove one 201/one 409 for the same free nights; both orders for booking versus block, Host/Admin removal, and cancellation/rebooking; committed price/approval/window rechecks; identical simultaneous cancellations; and arrival/cancellation cutoff rechecks after waiting. Commit-failure tests prove full rollback without partially accepted reservations or cancellation state.

Two test-only lint findings (assigned lambdas) were fixed. The initial cancellation failures are retained above as actual results; all final gates pass. Manual React search → book → history → cancel and browser acceptance remain unexecuted pending teammate integration. GitHub CI has not run for this unpushed phase. Earlier plans' external placeholders (course timezone/Demo Day, team/board/instructor links, shared API review) remain pending and do not block local backend work.

### Handoff and checkpoint

The [booking walkthrough and contract](bookings.md) and [frontend JSON examples](fixtures/bookings.json) are ready for teammate review. Price/inventory can change after a search quote; the accepted server confirmation is authoritative. Existing seed snapshot text is retained as stored, without invented historical backfill. No frontend files, cloud resources, paid services, or unrelated user data were changed. New writes were verified against disposable schemas in the separate test database; the live development smoke check only logged in and read bookings.

The user subsequently authorized committing and pushing Phase 6 on `backend/bookings-cancellation`. Checkpoint message: `feat: add atomic Customer bookings, history, and cancellation`. Git history records the final commit identifier; GitHub CI results are tracked separately after push.

## Next phase

Phase 7 will implement Customer review creation and paginated public listing reviews. It will enforce ownership, a noncancelled checked-out stay, one review per booking (including concurrent duplicate requests), and 1–5 ratings, reusing the existing public rating aggregates. Phase 7 has not started.
