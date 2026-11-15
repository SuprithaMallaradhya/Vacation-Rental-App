# Requirement coverage

Phase 0 records the complete assignment coverage; later phases will replace placeholders with exact source/test links. Phase 1 intentionally covers only foundation requirements.

| ID | Requirement | Phase 0 evidence | Phase 1 evidence/status |
|---|---|---|---|
| R01 | JSON inputs/outputs, validation, errors | `docs/api-contract.md` | `backend/app/middleware/errors.py`; foundation test covers 404 envelope |
| R02 | Customer/Host registration and login | Backlog item AUTH-01 | Phase 3 |
| R03 | Date/time/guest/duration/availability search | Backlog item SEARCH-01 | Phases 2–6 |
| R04 | City/state/ZIP search | Backlog item SEARCH-01 | Phase 5 |
| R05 | Google address search/map display | External checks | Phase 9; no key required locally |
| R06 | Media/amenities/cost/reviews/booked-today | Backlog item LIST-01 | Phases 4–7 |
| R07 | Booking and overlap prevention | Backlog item BOOK-01 | Phase 6 |
| R08 | Cancellation | Backlog item BOOK-02 | Phase 6 |
| R09 | Past-stay reviews | Backlog item REVIEW-01 | Phase 7 |
| R10–R15 | Host/Admin features and role access | Backlog items LIST-01, AUTH-01, ANALYTICS-01 | Phases 3–8 |
| R16 | Azure architecture | `docs/external-checks.md` | No provisioning authorized in Phase 1 |
| R17 | Database/mock listings | Backlog item DB-01 | Phase 2 |
| R18–R21 | Ownership, Scrum evidence, diagrams, final README | `docs/product-backlog.md` and placeholders | Ongoing; no fabricated evidence |
