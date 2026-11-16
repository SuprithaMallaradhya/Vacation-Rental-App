# Host and Admin analytics

Phase 8 adds read-only JSON analytics using the existing listings and booking snapshots. No migration/dependency/environment change is required; head stays `0002_listing_removal_audit`. No cloud or external provider is involved.

## Local setup and Swagger test

From the project root with Docker running and the existing database migrated/seeded:

```bash
make db-up
make api
```

Open `http://127.0.0.1:8000/docs` and the **analytics** group.

1. Log in at POST `/api/v1/auth/login` using `host1@example.test` / `DemoOnly!2026` (deliberately public local demo credentials). Authorize with `data.access_token`.
2. Execute GET `/api/v1/host/analytics` with period_days=30. Expect 200 and scope=HOST. Try 60 and 90; current listing inventory stays current while period booking/new-listing metrics can change.
3. Test an owned ZIP (copy text from your Host listing details). Try an unmatched valid ZIP such as `00000`: expect 200, zero totals/empty ZIP breakdowns, and zero-filled daily buckets.
4. With the Host token, GET `/api/v1/admin/analytics` must return 403.
5. Log in as `admin@example.test` with the same local demo password and replace the authorized token. GET `/api/v1/admin/analytics` must return 200 and scope=ADMIN, covering every Host. Try ZIP `02108` to check leading zeroes. Admin on the Host endpoint returns 403.
6. Invalid period_days=31 or zip_code=0210X must return JSON 422. Adding host_id or as_of must also return 422; scope/time cannot be supplied by the client. Clearing authorization gives 401.

Compare totals to their ZIP/day breakdowns using the rules below. Actual counts depend on retained local data; no fixed demo totals are promised. Existing seed dates are anchored to its initial run, so an older dataset may have empty period buckets without empty listing inventory. These GETs do not write data.

```bash
make test TEST_PATH=tests/analytics
make verify
make openapi
```

Tests use the separate local test database and disposable schemas. Both PostgreSQL services must run, and development migrations must already exist for the drift check.

## Routes and filters

| Route | Required role | Scope |
|---|---|---|
| GET `/api/v1/host/analytics` | HOST | Only listings owned by the authenticated Host, and their bookings |
| GET `/api/v1/admin/analytics` | ADMIN | All listings/Hosts and retained bookings |

Both return `{"success":true,"data":...}`. Allowed query fields are only period_days (30, 60, or 90; default 30) and optional exact zip_code (five digits or ZIP+4, text). Unknown query fields are rejected. Missing/invalid tokens return 401, wrong roles 403, validation errors 422, all with the standard error envelope and matching X-Request-ID. Customer tokens cannot access either endpoint. There is no client-selected Host or reporting clock.

## Metric definitions

Each response supplies scope, period_days, zip_code, window_start, window_end, timezone=UTC and currency=USD. The server captures one window_end and uses **[window_end − period_days, window_end)**, including the start and excluding the end. The duration is exactly 30/60/90 × 24 hours in UTC, including across daylight-saving transitions.

| Field | Definition |
|---|---|
| total_listings | Current scoped inventory, including PENDING/APPROVED/REJECTED/REMOVED |
| listing_status_counts | Counts for all four states, including zeroes; sum equals total_listings |
| new_listings_in_period | Those scoped listings whose created_at falls in the reporting window |
| rentals_by_zip | Current listing counts grouped by current ZIP, sorted by ZIP |
| bookings_created | Bookings created in the window, even if subsequently cancelled |
| cancelled_bookings | Currently cancelled subset of bookings_created, regardless of cancellation date |
| net_bookings | Noncancelled subset; includes ongoing and completed stays |
| booking_value_usd | Sum of noncancelled total_cost snapshots from bookings_created; **booking value, not paid revenue** |
| bookings_by_zip | The same four booking metrics grouped by saved booking ZIP, sorted by ZIP |
| daily_bookings | The same four booking metrics grouped by UTC creation date, ascending, with zeroes for missing dates |

This is a creation-window report with current cancellation/listing states, not a count of stays occurring in the period or cancellation events during the period. Old bookings cancelled recently are excluded if their creation was outside the window. Future and completed accepted stays count when their creation belongs to the window. Listing removal does not erase history. Current price edits cannot change past booking value. All money serializes as two-decimal strings, including `"0.00"`; aggregate sums can exceed a single booking's NUMERIC range.

ZIP filtering is deliberately different for the two populations: listing metrics use current Listing.zip_code; booking metrics use Booking.listing_zip_snapshot. A moved/removed property's bookings can contribute to an old ZIP with zero current inventory there. Listing counts and booking counts should not be expected to match. Host scoping still applies to both populations before aggregation, including historical/removed listings.

## Daily chart boundaries and reconciliation

Daily rows contain date plus window_start/window_end clipped to that UTC calendar date's intersection with the reporting window. A midnight window_end touches exactly period_days dates. A non-midnight window normally touches **period_days + 1** dates because both edge dates are partial. Do not change the rolling window to midnight or drop an edge bucket to force a 30-bar chart.

For example, `[2026-10-17T12:30Z, 2026-11-16T12:30Z)` is exactly 30 days but touches 31 UTC dates. The first bucket begins Oct 17 at 12:30; the last ends Nov 16 at 12:30. Every date in between is a complete UTC day. No bucket extends outside the reporting interval, and consecutive bucket bounds are contiguous. The current partial date is intentional, not a future-day zero.

For each of bookings_created/cancelled_bookings/net_bookings/booking_value_usd, summing either bookings_by_zip or daily_bookings equals the top-level metric. Each row also obeys bookings_created − cancelled_bookings = net_bookings. rentals_by_zip and listing_status_counts each sum to total_listings. ZIP breakdowns contain populated groups; daily rows contain every intersecting date even with zero bookings.

## Implementation and handoff

One grouped PostgreSQL UNION ALL statement reads listing ZIP/status/new counts and booking UTC-date/snapshot-ZIP counts/value from one statement snapshot. The booking branch joins only its owning listing to enforce Host scope; it never joins reviews/media that could multiply counts. Root booking totals and both booking chart breakdowns derive from those same grouped rows, avoiding disagreement during concurrent writes. UTC conversion is explicit and independent of the PostgreSQL session or listing timezone. No raw customer, booking, or listing identifiers/profiles are returned.

Use [analytics JSON fixtures](fixtures/analytics.json), the schema, and the metric definitions for React. The fixtures include complete 30-day daily arrays, both scopes, empty data, and error examples. The chart labels should use “Booking value (USD)”, “Bookings created”, “Cancelled bookings”, “Net bookings”, and “Current listings”. Shared Host/Admin dashboard acceptance and browser verification remain pending; see the [phase audit](phase-acceptance.md). No React screens were created or changed in this phase.

References: [PostgreSQL aggregate filters](https://www.postgresql.org/docs/16/sql-expressions.html#SYNTAX-AGGREGATES), [PostgreSQL date/time conversion](https://www.postgresql.org/docs/16/functions-datetime.html), [SQLAlchemy SQL functions](https://docs.sqlalchemy.org/en/20/core/functions.html).
