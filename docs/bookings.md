# Customer bookings, history, and cancellation

Phase 6 adds Customer-only booking writes and saved confirmations using the existing schema. No new dependency or migration is required; Alembic head remains `0002_listing_removal_audit`.

## Local setup and Swagger walkthrough

From the repository root, with Docker running:

```bash
make db-up
make migrate
make seed
make api
```

Open `http://127.0.0.1:8000/docs`. Log in at POST `/api/v1/auth/login` using the deliberately public local demo account `customer1@example.test` / `DemoOnly!2026`. Click Authorize and paste `data.access_token`. These credentials are for the local fake dataset only.

1. Use public GET `/api/v1/listings/search` with a future check_in, duration_nights=2, guests=2. Copy an available listing's ID. Omit optional fields rather than sending empty strings.
2. Open POST `/api/v1/bookings`. Replace the illustrative UUID with that live ID and use the same selected dates/guests/times:

```json
{
  "listing_id": "11111111-1111-4111-8111-111111111111",
  "check_in": "2030-01-10",
  "duration_nights": 2,
  "guests": 2
}
```

3. Expect 201 and save `data.id`. Compare the accepted total and timestamps with the selected stay. Prices/inventory can change after search; the confirmation is authoritative.
4. Submit the same dates again: expect 409 DATES_UNAVAILABLE while the original remains confirmed. New dates starting on its check_out are allowed if otherwise available.
5. GET `/api/v1/bookings/my` and GET `/api/v1/bookings/{booking_id}` show your saved confirmation.
6. PATCH `/api/v1/bookings/{booking_id}/cancel` with no body before accepted arrival: expect 200 CANCELLED. Repeating it returns the same saved cancellation; dates are released for another valid booking.

Future example dates are illustrative and do not guarantee inventory. Manual writes create real local demo history. Automated tests run separately in disposable schemas in the isolated test database.

## Routes and request contract

| Method/path | Request | Success |
|---|---|---|
| POST `/api/v1/bookings` | JSON stay plus listing_id | 201 `success/data` confirmation |
| GET `/api/v1/bookings/my` | page >=1, page_size 1–50 (default 10) | 200 `success/data` array with top-level pagination |
| GET `/api/v1/bookings/{booking_id}` | Owned booking UUID | 200 `success/data` confirmation |
| PATCH `/api/v1/bookings/{booking_id}/cancel` | Owned UUID; no body | 200 `success/data` confirmation |

All four require a Customer bearer token. Missing/invalid auth is 401, Host/Admin access is 403, and foreign/missing booking IDs share the same 404. History always scopes to the authenticated Customer; it cannot be overridden with customer_id. `/my` is registered before the UUID path. History includes confirmed, completed, cancelled, and removed-listing bookings, newest creation first with ascending UUID ties. Out-of-range pages are empty with unchanged totals.

Creation accepts only listing_id, check_in, check_out and/or duration_nights, optional check_in_time/check_out_time, and guests (default 1). Dates are strict YYYY-MM-DD and times listing-local HH:MM. Checkout and duration must agree; stays are 1–14 local nights. Unknown fields are rejected, including customer_id, total_cost, nightly_price_snapshot, currency, and reservation_state. The server derives ownership, price, currency, timestamps, and state.

Shared [stay and availability rules](public-search.md) apply to capacity, allowed weekdays/windows, default times, past arrivals, DST gaps/folds, Decimal total range, and half-open nightly inventory. Changing arrival/departure times cannot bypass a reserved night. Cancelled reservations release inventory; Host date blocks still apply.

## Confirmation fields and history

The same response model is used for create/detail/history/cancel. See the [JSON examples](fixtures/bookings.json).

| Fields | Meaning |
|---|---|
| id / listing_id | Saved booking UUID and original listing UUID |
| check_in / check_out / nights / guests | Accepted local dates, exclusive checkout, local night count, and guests |
| check_in_time / check_out_time | HH:MM derived from accepted UTC times using the saved timezone |
| arrival_at / departure_at | Accepted UTC timestamps |
| nightly_price_snapshot / total_cost / currency | Saved server-calculated Decimal strings and USD; total = nights × nightly price |
| listing_name_snapshot / listing_address_snapshot / listing_zip_snapshot / listing_timezone_snapshot | Accepted location/name fields, retained after edits or removal |
| reservation_state | Persisted CONFIRMED or CANCELLED |
| status | CANCELLED first; otherwise COMPLETED at/after departure_at, CONFIRMED before departure |
| can_cancel | True only for a noncancelled booking strictly before arrival_at |
| created_at / updated_at / cancelled_at | UTC audit timestamps; cancelled_at null until cancellation |

COMPLETED is computed when reading, without a scheduler or persisted state change. An ongoing stay remains CONFIRMED but can_cancel=false. Cancelling is allowed strictly before accepted arrival, closes exactly at arrival, and never changes accepted prices/dates/snapshots. Repeated cancellation remains idempotent even after the former arrival time. Listing removal does not silently cancel guests or prevent a valid future owner cancellation. No booking is hard-deleted.

Use saved confirmation fields to render history, including removed listings; public listing detail may now return 404. No customer profile, Host account ID, password, or moderation data is returned. Earlier seed confirmations preserve their original stored address representation; no historical snapshots are backfilled.

## Transactions and errors

Creation locks and refreshes the listing first, reads current rules/inventory, checks the clock after waiting, validates current approval/price/stay, inserts accepted snapshots, and commits once. Cancellation reads only the owned parent ID, locks the listing before the booking, refreshes state, checks the current clock, and atomically records cancellation. Failed writes roll back. Host blocks/edits and Admin moderation/removal already use the same listing-first lock order.

Locks live in PostgreSQL and work across API processes. The existing GiST exclusion constraint independently rejects confirmed nightly overlaps; that named constraint is translated into a safe 409 instead of exposing SQL. Concurrency tests use separate sessions/connections and observe `pg_blocking_pids` to prove an actual lock wait, without process-local mutexes.

| HTTP/code | Meaning |
|---|---|
| 400 INVALID_JSON | Malformed JSON |
| 401 UNAUTHENTICATED / 403 FORBIDDEN | Missing/invalid token or wrong role |
| 404 NOT_FOUND | Missing listing on creation, or missing/foreign owned booking |
| 409 LISTING_UNAVAILABLE | Existing listing is not approved for new bookings |
| 409 DATES_UNAVAILABLE | Confirmed nightly overlap or Host block; no reservation inserted |
| 409 CANCELLATION_CLOSED | Noncancelled stay has reached accepted arrival |
| 422 VALIDATION_ERROR / stay-specific codes | Bad fields/dates/duration, capacity/window/DST/past/total-range failure |

Errors use the shared JSON envelope and request ID. Booking creation is not an idempotency-key API: duplicate occupied requests return 409. After a network timeout, refresh your history before deciding whether another request is needed. Search quotes are estimates; render the server's accepted price in the confirmation.

## Verification and frontend handoff

```bash
make test TEST_PATH=tests/bookings
make verify
make openapi
```

Tests cover search → book → history → cancel, ownership/roles, 1/14-night boundaries, blocks, back-to-back dates, cancelled inventory, snapshots, checkout/cancellation boundaries, DST, commit rollback, exclusion-constraint errors, and real competing transactions. Shared React search → book → history → cancel and manual browser acceptance remain pending teammate integration. Review creation/public review pages remain Phase 7.

References: [SQLAlchemy async session concurrency](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-asyncsession-with-concurrent-tasks), [PostgreSQL row locks](https://www.postgresql.org/docs/16/explicit-locking.html#LOCKING-ROWS).
