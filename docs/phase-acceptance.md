# Backend phase acceptance audit

Added during Phase 7 to compare milestones against the implementation plan. [Implementation status](implementation-status.md) records actual commands and results. Historical failures are retained; later passing gates supersede earlier runtime limitations. This is backend evidence, not a claim of React, course, or cloud acceptance.

| Phase | Checks and evidence | Remaining shared/external work |
|---|---|---|
| 0: preparation | Backlog IDs/acceptance/estimates/owners/sprints, API contract, coverage, decisions, external checks, local repository instructions | Team/instructor links and actual teammate contract review |
| 1: foundation | `backend/tests/foundation/`: settings/isolation, health/readiness during simulated outage, JSON errors/request IDs/docs; exact CORS and PostgreSQL CI configured | Actual stop/restart recovery is recorded at Phase 2; deployment is later |
| 2: schema/data | `backend/tests/database/`: fresh migrations, checks/FKs/indexes, guarded insert-only seed, snapshots/UTC/ZIP/Decimal, ERD | Demo data may need explicit shared rehearsal preparation |
| 3: auth | `backend/tests/auth/`: signup/all-role JSON login, bcrypt/JWT/expiry, roles/ownership, injection/privacy/log safety, basic throttle | React token/error handling acceptance; deployment shared throttle |
| 4: Host/Admin | `backend/tests/listings/`: lifecycle/media/hours/windows/blocks, nested ownership, approval/reapproval, audited removal, rollback/history, future-stay protections and queued writers | Shared management UI acceptance |
| 5: search | `backend/tests/search/`: individual/AND filters, 1/14 vs 0/15 nights, defaults/windows/inventory/quotes, null browse, radius/ZIP, sorting/pagination, cost/ratings/local daily counts, DST/privacy | Shared search/detail UI; live Google remains Phase 9 |
| 6: bookings | `backend/tests/bookings/`: atomic server-priced snapshots, owned history/detail/cancel, exact time boundaries, preserved confirmations; actual PostgreSQL competing booking/block/removal/cancellation and rollback checks | Shared booking/history/cancel UI |
| 7: reviews | `backend/tests/reviews/`: owned checked-out noncancelled eligibility, duplicate protection, public privacy, rating aggregates, null/empty results, pagination, concurrency, boundaries and rollback | Shared review UI and successful manual demo submission |

The latest targeted phase suite is followed by the complete backend suite, lint, and migration drift checks. See the Phase 7 status for actual results. Passing tests establish their covered scenarios, not an absence of every possible defect.

The Phase 7 full regression exposed a flaky older raw-insert exclusion-constraint test: simultaneous inserts could deadlock before one reached the expected conflict. The test now holds one uncommitted inserted row, observes the second transaction's actual constraint wait, then commits and verifies one retained booking/one constraint rejection. This does not introduce an application lock into the constraint test or weaken the constraint. Phase 6's actual simultaneous booking API tests continue separately.

## Endpoint completeness

The audit parsed the plan's Phase 3–7 endpoint inventory and compared normalized method/path pairs with generated OpenAPI. All **34 planned product operations** are present, plus the documented protected Host amenities helper (**35 total**). `/health` and `/ready` are also present. Behavior/authorization tests are separate evidence. Phase 8 analytics endpoints remain unimplemented.

## Explicit outstanding items

- Shared React flows/browser acceptance, teammate contract review, and a reachable API base URL remain pending. Localhost alone is not a cross-machine handoff.
- Every eligible original seed stay already has a review. A successful manual submission needs an owned completed unreviewed stay; automated tests prepare that case only in disposable schemas. Shared demo data preparation remains pending without rewriting accepted history.
- Course timezone/Demo Day/evaluation window, team/member names, task board, instructor sheet, genuine Scrum/burndown/journal evidence require team/instructor input. Git commits do not prove meetings or reviews.
- Phase 8 analytics, Phase 9 Google Maps, Phase 10 production packaging/templates, later budget-gated deployment and final evidence remain future milestones. No cloud resources or paid services were created.
- GitHub CI results must be checked for each pushed commit; local tests do not prove remote CI success. Existing CI discovers all backend tests without deployment.

See the [external-check register](external-checks.md). These items remain visible and do not block independent local backend work.
