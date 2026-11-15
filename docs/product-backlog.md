# Product backlog

Owners are intentionally placeholders until the team confirms names. Estimates are engineering estimates in ideal hours; priorities use Must/Should/Could.

| ID | Requirement / acceptance criteria | Owner | Priority | Estimate | Sprint |
|---|---|---|---|---:|---|
| FOUND-01 | Repository conventions, local commands, budget guardrails documented | `[PENDING: backend owner]` | Must | 2 | S1 |
| FOUND-02 | API/error/auth/date contract reviewed and versioned | `[PENDING: backend + frontend owners]` | Must | 3 | S1 |
| DB-01 | Fresh PostgreSQL database migrates with required tables, FKs, constraints, indexes | `[PENDING: backend owner]` | Must | 12 | S1 |
| DB-02 | Idempotent guarded seed creates realistic roles/listings/bookings/reviews without production reset | `[PENDING: backend owner]` | Must | 6 | S1 |
| AUTH-01 | Customer/Host JSON registration, login, `/auth/me`, expiring JWT, bcrypt, no admin signup | `[PENDING: backend owner]` | Must | 10 | S1 |
| LIST-01 | Host CRUD/media/hours/windows/blocks with ownership and moderation transitions/audit | `[PENDING: backend owner]` | Must | 18 | S2 |
| SEARCH-01 | Public approved-listing search/details/availability honors city/state/ZIP filters, 1–14 nightly dates, windows, capacity, blocks | `[PENDING: backend owner]` | Must | 16 | S2 |
| BOOK-01 | Atomic locked booking calculates server total and prevents overlaps under concurrency | `[PENDING: backend owner]` | Must | 18 | S2 |
| BOOK-02 | Customer history/detail/cancel is owner-only, future-only, idempotent, snapshot-preserving | `[PENDING: backend owner]` | Must | 8 | S2 |
| REVIEW-01 | One eligible customer review per past noncancelled stay with aggregate rating/count | `[PENDING: backend owner]` | Must | 8 | S3 |
| ANALYTICS-01 | Host/Admin 30/60/90-day UTC metrics with ZIP and zero-filled buckets | `[PENDING: backend owner]` | Should | 12 | S3 |
| UI-01 | React connects auth, search, details, booking, history, cancellation, reviews | `[PENDING: frontend owner]` | Must | 20 | S3 |
| UI-02 | React connects Host/Admin workflows and analytics; loading/error/forbidden states | `[PENDING: frontend owner]` | Must | 16 | S3 |
| MAP-01 | Google address selection and map display with restricted key/quota | `[PENDING: frontend + backend owners]` | Must | 8 | S3 |
| DEPLOY-01 | Production-like local package and Azure VMSS/LB/PostgreSQL templates within budget gate | `[PENDING: backend owner]` | Must | 20 | S4 |
| EVID-01 | Diagrams, genuine journal, sprint artifacts, burndown link, contribution evidence, demo | `[PENDING: both owners]` | Must | 12 | S4 |

## External-check register

| Check | Needed by | Status |
|---|---|---|
| Confirm course timezone and Demo Day | Final handoff | `[PENDING: instructor/course materials]` |
| Confirm team names, repository, board, burndown sheet | Phase 0/final evidence | `[PENDING: team]` |
| Verify Python 3.12 and Docker-compatible local runtime | Phase 1 | Phase 2 follow-up passed: Python 3.12.16, both Compose databases, migrations/seed, 41 tests, lint, drift check, live health/readiness and outage/recovery |
| Verify Azure Student eligibility, regional prices, quota, private PostgreSQL networking, TLS/DNS | Phase 10/11 | Not blocking local work; no resources provisioned |
| Verify Google Maps billing/free allowance and key restrictions | Phase 9 | Not blocking backend work; no key used |
