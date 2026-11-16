# Requirement coverage

Coverage reflects implemented backend Phases 0–5. Later API phases and shared frontend acceptance remain explicitly pending.

| ID | Requirement | Planning evidence | Current implementation/evidence |
|---|---|---|---|
| R01 | JSON inputs/outputs, validation, errors | `docs/api-contract.md` | Phase 3 auth request/response models, safe validation errors, preserved authentication/throttle headers, and `backend/tests/auth/` tests |
| R02 | Customer/Host registration and login | Backlog item AUTH-01 | Phase 3 implemented and tested for Customer/Host/seeded Admin: `backend/app/routers/auth.py`, `services/auth.py`, and `backend/tests/auth/`; React check pending |
| R03 | Date/time/guest/duration/availability search | Backlog item SEARCH-01 | Phase 5 `schemas/search.py`, `services/availability.py`, `services/search.py`, and `tests/search/`: 1–14 nights, duration agreement, windows/capacity, past arrival, DST, inventory, indicative quotes |
| R04 | City/state/ZIP search | Backlog item SEARCH-01 | Phase 5 filters individually and combined with AND semantics, leading-zero ZIP, empty results and stable pagination tested |
| R05 | Google address search/map display | External checks | Phase 5 numeric coordinates and bounded Haversine radius implemented/tested; live Google address selection/map UI remains Phase 9; no key required locally |
| R06 | Media/amenities/cost/reviews/booked-today | Backlog item LIST-01 | Phase 4 management plus Phase 5 public cards/details, media/amenities, cost boundaries, eligible review aggregates/null average, listing-local daily counts; review creation/content APIs remain Phase 7 and UI acceptance pending |
| R07 | Booking and overlap prevention | Backlog item BOOK-01 | Phase 2 exclusion constraint; Phase 4 listing-first locks; Phase 5 shared stay/inventory validator with half-open/cancelled/block tests; booking transactions and races remain Phase 6 |
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
