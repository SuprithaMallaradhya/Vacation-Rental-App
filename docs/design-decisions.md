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

## Pending external confirmations

- `[PENDING: team name and member names]`
- `[PENDING: assigned GitHub repository/board link]`
- `[PENDING: instructor burndown-sheet link and course timezone/Demo Day]`
- `[PENDING: teammate review of API field names and error envelope]`
