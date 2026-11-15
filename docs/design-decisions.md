# Design-decision log

| Date | Decision | Reason / consequence | Status |
|---|---|---|---|
| 2026-11-15 | V2 is authoritative for implementation | Resolves older conflicts and preserves confirmed nightly-stay, budget, and ownership decisions | Confirmed |
| 2026-11-15 | Python 3.12 with pinned dependencies in `backend/pyproject.toml` | Reproducible local and CI setup | Confirmed |
| 2026-11-15 | Development PostgreSQL initially used port 5432; test PostgreSQL used 5433 | Superseded by the conflict-free Phase 2 ports below | Superseded |
| 2026-11-15 | `/health` is process-only; `/ready` checks SQL connectivity, the expected revision, and required tables | A version table alone does not prove schema readiness | Implemented |
| 2026-11-15 | CORS allows exactly `http://localhost:5173` and `http://127.0.0.1:5173` in development | Matches the planned React dev server without wildcard access | Implemented |
| 2026-11-15 | Request IDs are accepted from `X-Request-ID` or generated and returned in a response header and error body | Supports tracing without exposing secrets | Implemented |
| 2026-11-15 | No cloud provisioning in Phases 0–1 | Local-first development and $10 Azure credit ceiling | Confirmed |
| 2026-11-15 | Bind project PostgreSQL services to `127.0.0.1:55432` (development) and `127.0.0.1:55433` (test) | Native PostgreSQL was already listening on 5432; explicit loopback bindings avoid the collision and LAN exposure | Implemented in Phase 2 |
| 2026-11-15 | Named checks with portable string enums; UUID keys, UTC timestamps, text ZIPs, Decimal money | Preserves clear migration diffs and domain constraints on PostgreSQL | Implemented in Phase 2 |
| 2026-11-15 | Persist only CONFIRMED/CANCELLED bookings with listing/price/time snapshots; use DATE blocks | Applies confirmed technical corrections to older V2 draft schema wording; completion is derived in a later service | Implemented in Phase 2 |
| 2026-11-15 | GiST exclusion constraint using `btree_gist` for confirmed nightly overlaps | Adds database protection; transactional listing locks and booking/block/moderation race tests are still Phase 6 requirements | Implemented in Phase 2 |
| 2026-11-15 | Each database test migrates a new UUID schema inside the isolated local test database | Tests exercise real migrations without resets, shared-table truncation, or development connections | Implemented in Phase 2 |
| 2026-11-15 | Seed deterministic IDs and insert missing rows only; anchor relative dates to initial dataset creation | Reruns neither duplicate nor rewrite demo edits/history; seed CLI refuses nonlocal/nondevelopment targets | Implemented in Phase 2 |
| 2026-11-15 | bcrypt 5.0.0 hashes the deliberately public local demo password | Produces real hashes for Phase 3 login; no auth endpoints or JWT handling are implemented early | Implemented in Phase 2 |
| 2026-11-15 | Phase 3 uses JSON login plus HTTPBearer in Swagger | Matches the React contract; does not add an OAuth form-login dependency | Implemented in Phase 3 |
| 2026-11-15 | PyJWT 2.15.1 with fixed HS256, issuer/audience, required claims and expiry | Rejects unsigned/wrong-algorithm/expired/malformed tokens; current roles are loaded from PostgreSQL per request | Implemented in Phase 3 |
| 2026-11-15 | Generate an ephemeral process key only for development/test when no signing secret is configured | Avoids a shared public default; restart invalidates local tokens. Nonlocal environments require an explicit key of at least 32 UTF-8 bytes | Implemented in Phase 3 |
| 2026-11-15 | Validate email syntax without DNS using email-validator 2.4.0; allow .test demo addresses | Trim/lowercase and ASCII-normalize domains consistently; reject internationalized local parts for this prototype | Implemented in Phase 3 |
| 2026-11-15 | Signup passwords are 8–72 UTF-8 bytes, login 1–72; bcrypt runs in a worker thread | Prevents silent truncation and event-loop blocking; login failures perform bcrypt work for unknown accounts | Implemented in Phase 3 |
| 2026-11-15 | Enforce a bounded process-local sliding login window (10 attempts/IP/60 seconds by default) | Basic protection within scope; no shared service added. Deployment must add a shared/edge limit and configure trusted proxies | Implemented in Phase 3 |
| 2026-11-15 | Server assigns signup roles and rejects unknown JSON fields; DB uniqueness handles concurrent normalized emails | Prevents role injection and duplicate-account races; Admin is seed-only | Implemented in Phase 3 |
| 2026-11-15 | Log unexpected exception class and request ID without raw exception text/SQL parameters | Prevents credentials or password hashes from appearing in failure logs; preserves generic JSON 500 responses and request IDs | Implemented in Phase 3 |
| 2026-11-15 | Move PostgreSQL migration/seed fixtures into shared test support | Auth and database tests use the same guarded isolated-schema harness; no new migration is needed for auth | Implemented in Phase 3 |

## Pending external confirmations

- `[PENDING: team name and member names]`
- `[PENDING: assigned GitHub repository/board link]`
- `[PENDING: instructor burndown-sheet link and course timezone/Demo Day]`
- `[PENDING: teammate review of API field names and error envelope]`
