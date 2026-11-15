# Requirement coverage

Phase 0 records the complete assignment coverage; later phases will replace placeholders with exact source/test links. Phase 1 intentionally covers only foundation requirements.

| ID | Requirement | Phase 0 evidence | Phase 1 evidence/status |
|---|---|---|---|
| R01 | JSON inputs/outputs, validation, errors | `docs/api-contract.md` | Phase 3 auth request/response models, safe validation errors, preserved authentication/throttle headers, and `backend/tests/auth/` tests |
| R02 | Customer/Host registration and login | Backlog item AUTH-01 | Phase 3 implemented and tested for Customer/Host/seeded Admin: `backend/app/routers/auth.py`, `services/auth.py`, and `backend/tests/auth/`; React check pending |
| R03 | Date/time/guest/duration/availability search | Backlog item SEARCH-01 | Phase 2 date/window models and 1/14 versus 0/15-night database tests in `backend/tests/database/test_schema.py`; search services remain Phases 4–6 |
| R04 | City/state/ZIP search | Backlog item SEARCH-01 | Phase 5 |
| R05 | Google address search/map display | External checks | Phase 9; no key required locally |
| R06 | Media/amenities/cost/reviews/booked-today | Backlog item LIST-01 | Phases 4–7 |
| R07 | Booking and overlap prevention | Backlog item BOOK-01 | Phase 2 exclusion constraint and two-transaction integration test; listing locks and booking APIs/race checks remain Phase 6 |
| R08 | Cancellation | Backlog item BOOK-02 | Phase 6 |
| R09 | Past-stay reviews | Backlog item REVIEW-01 | Phase 7 |
| R10–R14 | Host/Admin features and analytics | Backlog items LIST-01, ANALYTICS-01 | Phases 4–8 |
| R15 | Backend/frontend role access | Backlog item AUTH-01 | Phase 3 JWT/current-role and ownership dependencies tested with all three roles; resource-specific enforcement comes with later endpoints; React acceptance pending |
| R16 | Azure architecture | `docs/external-checks.md` | No provisioning authorized in Phase 1 |
| R17 | Database/mock listings | Backlog items DB-01/DB-02 | Phase 2 implemented: `backend/app/models/`, initial Alembic revision, `backend/seed/demo.py`; 28 PostgreSQL tests pass |
| R18–R21 | Ownership, Scrum evidence, diagrams, final README | `docs/product-backlog.md` and placeholders | Ongoing; no fabricated evidence |

Phase 2 ERD source/export are `docs/diagrams/erd.mmd` and `docs/diagrams/erd.svg` (part of R20). Component/deployment diagrams, wireframes, and shared UI acceptance remain scheduled for later phases.
