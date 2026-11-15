# Requirement coverage

Phase 0 records the complete assignment coverage; later phases will replace placeholders with exact source/test links. Phase 1 intentionally covers only foundation requirements.

| ID | Requirement | Planning evidence | Current implementation/evidence |
|---|---|---|---|
| R01 | JSON inputs/outputs, validation, errors | `docs/api-contract.md` | Phase 3 auth request/response models, safe validation errors, preserved authentication/throttle headers, and `backend/tests/auth/` tests |
| R02 | Customer/Host registration and login | Backlog item AUTH-01 | Phase 3 implemented and tested for Customer/Host/seeded Admin: `backend/app/routers/auth.py`, `services/auth.py`, and `backend/tests/auth/`; React check pending |
| R03 | Date/time/guest/duration/availability search | Backlog item SEARCH-01 | Phase 2 date/window models and 1/14 versus 0/15-night tests; Phase 4 weekly rules/blocks and future-window protection; search services remain Phases 5–6 |
| R04 | City/state/ZIP search | Backlog item SEARCH-01 | Phase 5 |
| R05 | Google address search/map display | External checks | Phase 9; no key required locally |
| R06 | Media/amenities/cost/reviews/booked-today | Backlog item LIST-01 | Phase 4 Host media/amenities and cost-rating boundaries implemented; public cards/details and ratings/booked-today remain Phases 5–7 |
| R07 | Booking and overlap prevention | Backlog item BOOK-01 | Phase 2 exclusion constraint; Phase 4 shared listing-row lock, concurrent blocks, queued writer removal test; booking APIs and booking/block races remain Phase 6 |
| R08 | Cancellation | Backlog item BOOK-02 | Phase 6 |
| R09 | Past-stay reviews | Backlog item REVIEW-01 | Phase 7 |
| R10–R11 | Host add/remove/view/update own listings and nested resources | Backlog item LIST-01 | Phase 4 `routers/host.py`, `schemas/listings.py`, `services/listings.py`, and `tests/listings/`; history and nested ownership verified |
| R12 | Host own analytics | Backlog item ANALYTICS-01 | Phase 8 |
| R13 | Admin approve/reject/remove listings and audit | Backlog item LIST-01 | Phase 4 `routers/admin.py`, approval validation, atomic audit/rollback, removal history, and tests implemented |
| R14 | Admin analytics | Backlog item ANALYTICS-01 | Phase 8 |
| R15 | Backend/frontend role access | Backlog item AUTH-01 | Phase 3 auth plus Phase 4 role/ownership matrix for every Host/Admin operation and nested child IDs; React acceptance pending |
| R16 | Azure architecture | `docs/external-checks.md` | No provisioning authorized in Phase 1 |
| R17 | Database/mock listings | Backlog items DB-01/DB-02 | Phase 2 implemented: `backend/app/models/`, initial Alembic revision, `backend/seed/demo.py`; 28 PostgreSQL tests pass |
| R18–R21 | Ownership, Scrum evidence, diagrams, final README | `docs/product-backlog.md` and placeholders | Ongoing; no fabricated evidence |

ERD source/export are `docs/diagrams/erd.mmd` and `docs/diagrams/erd.svg` (part of R20), updated in Phase 4 for listing removals. Component/deployment diagrams, wireframes, and shared UI acceptance remain scheduled for later phases.
