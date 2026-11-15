# Design-decision log

| Date | Decision | Reason / consequence | Status |
|---|---|---|---|
| 2026-11-15 | V2 is authoritative for implementation | Resolves older conflicts and preserves confirmed nightly-stay, budget, and ownership decisions | Confirmed |
| 2026-11-15 | Python 3.12 with pinned dependencies in `backend/pyproject.toml` | Reproducible local and CI setup | Confirmed |
| 2026-11-15 | Development PostgreSQL is port 5432/database `vacation_rental_dev`; test PostgreSQL is port 5433/database `vacation_rental_test` | Prevents default tests from targeting development data | Implemented |
| 2026-11-15 | `/health` is process-only; `/ready` checks SQL connectivity and `alembic_version` | Load balancers can distinguish process health from schema readiness; migrations remain Phase 2 | Implemented |
| 2026-11-15 | CORS allows exactly `http://localhost:5173` and `http://127.0.0.1:5173` in development | Matches the planned React dev server without wildcard access | Implemented |
| 2026-11-15 | Request IDs are accepted from `X-Request-ID` or generated and returned in a response header and error body | Supports tracing without exposing secrets | Implemented |
| 2026-11-15 | No cloud provisioning in Phases 0–1 | Local-first development and $10 Azure credit ceiling | Confirmed |

## Pending external confirmations

- `[PENDING: team name and member names]`
- `[PENDING: assigned GitHub repository/board link]`
- `[PENDING: instructor burndown-sheet link and course timezone/Demo Day]`
- `[PENDING: teammate review of API field names and error envelope]`
