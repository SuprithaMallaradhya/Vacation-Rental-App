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
| 2026-11-15 | Phase 4 starts on `backend/listings-moderation` from merged main `670953f` | Keeps the new milestone separate from the merged auth branch | Implemented in Phase 4 |
| 2026-11-15 | Every listing/child/moderation mutation locks and refreshes the listing row first | Serializes updates across processes; future booking/cancellation writers must use the same helper/order | Implemented in Phase 4 |
| 2026-11-15 | Add `listing_removals` in additive migration `0002_listing_removal_audit` | Records both Host and Admin actors/reasons without misusing the Admin-only audit table; no invented legacy backfill | Implemented in Phase 4 |
| 2026-11-15 | Host/Admin listing DELETE requires a JSON reason and is idempotent/terminal | Keeps reservations/reviews and the original removal record; Admin removals additionally create an admin_actions row | Implemented in Phase 4 |
| 2026-11-15 | Drafts validate supplied core fields but may omit description/contact/media/weekly rows until approval | Supports incremental Host forms while approval validates all required fields atomically | Implemented in Phase 4 |
| 2026-11-15 | Use full seven-day PUT replacements, local HH:MM, and separate contact hours versus stay windows | Avoids partial-week ambiguity; future accepted UTC times remain valid despite default-only changes | Implemented in Phase 4 |
| 2026-11-15 | Real material/photo changes reset approval; no-op patches preserve it | Price/contact/hours/rules/blocks remain nonmaterial; rejected listings return to pending on actual edits | Implemented in Phase 4 |
| 2026-11-15 | Protect future/ongoing noncancelled stays against location/timezone/capacity/window changes | Preserve accepted inventory and guest/time snapshots; location changes with no active future dependency remain possible | Implemented in Phase 4 |
| 2026-11-15 | Protect Host form amenity references at `/api/v1/host/amenities` | Shares reference IDs now without implementing the Phase 5 public amenities/search APIs early | Implemented in Phase 4 |
| 2026-11-15 | Paginated lists use top-level pagination and deterministic ordering; money strings and numeric coordinates | Aligns with the V2 envelope and React form/map needs | Implemented in Phase 4 |

## Phase 5 decisions

| Date | Decision | Reason / consequence | Status |
|---|---|---|---|
| 2026-11-15 | Create `backend/search-availability` from merged main `51054b2` | Isolates public search from the merged Phase 4 milestone | Implemented |
| 2026-11-15 | Public search/detail/availability expose only approved listings through explicit public models | Keeps customer, ownership, and moderation records private while publishing Host-managed contact fields | Implemented |
| 2026-11-15 | Share stay resolution and half-open inventory helpers across public APIs and future booking creation | One 1–14-night/window/capacity/DST policy; Phase 6 must still lock/reload/revalidate inventory and price atomically | Implemented |
| 2026-11-15 | Reject ambiguous/nonexistent local timestamps; use local date differences for nightly price | Avoids guessed DST offsets and 23/25-hour-day pricing errors; pin tzdata 2026.6 as system-data fallback | Implemented |
| 2026-11-15 | Default available_only=true with dates, false without; false includes inventory conflicts with indicative quotes | Browse has null quote/availability; capacity/window/DST-invalid stays still cannot be offered | Implemented |
| 2026-11-15 | All filters use AND; amenities are repeated reference UUIDs; Haversine radius is >0 through 500 km | Gives React a precise filter contract without another external service or paid key | Implemented |
| 2026-11-15 | Bulk-load related rows/aggregates and apply local eligibility/radius before final pagination | Correct totals and deterministic results for the small demo catalog; production-scale spatial pagination remains future work | Implemented |
| 2026-11-15 | Ratings require eligible checked-out reviews; bookings_today uses the full current listing-local date and noncancelled reservations | Matches planned display definitions across timezones without customer data | Implemented |

## Phase 6 decisions

| Date | Decision | Reason / consequence | Status |
|---|---|---|---|
| 2026-11-15 | Create `backend/bookings-cancellation` from merged main `21ed13a` | Isolates booking work from the merged Phase 5 milestone | Implemented |
| 2026-11-15 | Reuse the existing bookings schema, stay validator, inventory queries, and listing lock | Avoids duplicate business rules and unnecessary migration/dependency changes | Implemented |
| 2026-11-15 | Customer identity comes from auth; creation rejects client price/currency/state/snapshots | Server calculates the current price and persists accepted confirmation fields atomically | Implemented |
| 2026-11-15 | Cancellation reads an owned parent ID, then locks listing before booking | Same cross-process writer ordering as blocks/moderation; foreign IDs return 404 before acquiring their parent's inventory lock | Implemented |
| 2026-11-15 | Inject a clock callable and read it after waiting/validation queries | Creation/cancellation cannot use a stale request-start timestamp after waiting for a lock | Implemented |
| 2026-11-15 | Explicit cancellation UPDATE RETURNING writes all state/audit fields together | Preserves chosen UTC operation time even when a frozen clock equals created_at; avoids implicit async ORM refresh during serialization | Implemented |
| 2026-11-15 | Persist CONFIRMED/CANCELLED; derive COMPLETED and can_cancel from accepted UTC snapshots | Correct checkout/arrival boundaries without a scheduler; repeat cancellation preserves its original timestamp | Implemented |
| 2026-11-15 | Confirmation/history render saved fields without requiring current public listing detail | Keeps accepted price/name/location/time readable after changes or terminal removal; existing seed snapshots stay intact | Implemented |
| 2026-11-15 | Observe pg_blocking_pids in separate-connection concurrency tests | Proves actual database serialization and both writer orders; no process-local mutex or timing-only assertion | Implemented |

## Phase 7 decisions

| Date | Decision | Reason / consequence | Status |
|---|---|---|---|
| 2026-11-15 | Create `backend/reviews-ratings` from merged main `7fed27a` | Keeps the reviews milestone separate from merged Phase 6 | Implemented |
| 2026-11-15 | Reuse existing Review unique booking constraint with INSERT ON CONFLICT DO NOTHING RETURNING | Concurrent duplicates give one saved review and a safe 409; never overwrite or weaken the DB constraint | Implemented |
| 2026-11-15 | Lock listing then owned booking and read the clock afterward | Consistent writer order; accepted UTC checkout determines eligibility, including exact boundary and lock waits | Implemented |
| 2026-11-15 | Strict integer rating 1–5 and trimmed plain-text comment 1–2000 characters | Reject coercion, field injection, blank/oversize text and unsupported control characters before PostgreSQL | Implemented |
| 2026-11-15 | Public reviews expose only id/rating/comment/created_at on approved listings | Keeps customer profile and booking identities private; owner-only creation response includes their booking/listing IDs | Implemented |
| 2026-11-15 | Past-guest review eligibility survives listing removal/loss of approval | Preserves feedback rights/history while public pages remain hidden; no listing state is changed | Implemented |
| 2026-11-15 | Public pages and search/detail aggregates share eligible_reviews predicates | Noncancelled checked-out stays and nonfuture submissions produce consistent counts/averages without stored rating edits | Implemented |
| 2026-11-15 | Make the old raw exclusion test order its uncommitted inserts and observe a real PostgreSQL wait | Full regression found a raw GiST insert deadlock in the test. API booking concurrency remains independently tested under listing locks; no retries/skips or weakened constraints | Implemented |
| 2026-11-15 | Retain original already-reviewed demo stays; prepare unreviewed stays only in disposable tests | Verifies successful creation without rewriting accepted development history; shared manual demo data preparation remains pending | Implemented |

## Pending external confirmations

- `[PENDING: team name and member names]`
- Repository verified from origin: [Vacation Rental App](https://github.com/SuprithaMallaradhya/Vacation-Rental-App); `[PENDING: task-board link]`
- `[PENDING: instructor burndown-sheet link and course timezone/Demo Day]`
- `[PENDING: teammate review of API field names and error envelope]`
