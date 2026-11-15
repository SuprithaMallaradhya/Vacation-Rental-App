# Host listing management and Admin moderation

Phase 4 adds protected listing management and moderation APIs. Customer search/quotes are Phase 5, and booking creation is Phase 6. React integration is still pending.

## Setup and roles

```bash
make setup
make db-up
make migrate
make seed
make api
```

The additive migration `0002_listing_removal_audit` is required; `/ready` remains 503 for an older schema. It adds `listing_removals` and preserves existing data. The updated seed adds only one missing fake removal record on an existing Phase 2 dataset; a second run inserts zero rows.

Use Swagger at `http://127.0.0.1:8000/docs`. JSON-login as `host1@example.test`, `host2@example.test`, or `admin@example.test`, with public demo password `DemoOnly!2026`. Paste `data.access_token` into Authorize. Host and Admin routes enforce their specific role: an Admin is not automatically treated as a Host. Changing roles for a manual check requires authorizing with that account's token.

## Implemented routes

All paths below start with `/api/v1`. UUIDs are used for listing, media, block, and amenity IDs. Every route requires bearer authentication.

| Role | Method | Path | Result |
|---|---|---|---|
| Host | GET | `/host/amenities` | Reference IDs/names for listing forms |
| Host | POST | `/host/listings` | 201 full pending listing |
| Host | GET | `/host/listings` | Paginated own listings, including removed |
| Host | GET/PATCH/DELETE | `/host/listings/{id}` | Own detail, update, or audited soft removal |
| Host | PUT | `/host/listings/{id}/hours` | Replace all seven contact-hour weekdays |
| Host | PUT | `/host/listings/{id}/booking-rules` | Replace all seven arrival/departure weekdays |
| Host | GET/POST | `/host/listings/{id}/blocks` | Paginated blocks or 201 new block |
| Host | DELETE | `/host/listings/{id}/blocks/{block_id}` | JSON deletion confirmation |
| Host | POST | `/host/listings/{id}/media` | 201 new media row |
| Host | PATCH/DELETE | `/host/listings/{id}/media/{media_id}` | Update media or JSON deletion confirmation |
| Admin | GET | `/admin/listings` | Paginated all listings |
| Admin | GET | `/admin/listings/pending` | Paginated pending queue |
| Admin | GET | `/admin/listings/{id}` | Full moderation detail |
| Admin | PATCH | `/admin/listings/{id}/approve` | Approve a complete pending listing |
| Admin | PATCH | `/admin/listings/{id}/reject` | Reject a pending listing with a reason |
| Admin | DELETE | `/admin/listings/{id}` | Audited soft removal |
| Admin | GET | `/admin/audit-actions` | Paginated Admin actions; optional listing_id filter |

Host/Admin listing lists accept optional `status=PENDING|APPROVED|REJECTED|REMOVED`. All paginated lists use `page>=1`, `page_size=1..50` (default 10), deterministic timestamp/date plus UUID ordering, and top-level `pagination` with page/page_size/total_items/total_pages. `data` is the item array; empty results have total_pages=0. The Host scope always comes from the current user, never a request host_id.

Scalar listing writes and weekly replacements return full listing detail. Media POST/PATCH returns a media object; block POST returns a block object. Media/block DELETE returns `{"success":true,"data":{"id":"<uuid>","deleted":true}}`. Listing DELETE returns the retained listing detail, including removal information.

## Create and edit

Create requires valid name, address_line1, city, state (two letters), ZIP text, coordinates, IANA timezone, positive nightly_price, and positive max_guests. Currency is USD. Description/contact fields default to empty, and media, amenities, contact hours, and booking rules can be added later. Drafts are PENDING and not yet eligible for approval.

```json
{
  "name": "Sunny San Jose Home",
  "address_line1": "100 Example Lane",
  "city": "San Jose",
  "state": "CA",
  "zip_code": "95112",
  "latitude": "37.338200",
  "longitude": "-121.886300",
  "timezone": "America/Los_Angeles",
  "nightly_price": "150.00",
  "max_guests": 4
}
```

Use PATCH on the owned listing to fill description/contact_name/contact_email/contact_phone or update scalar fields and `amenity_ids`. Unknown/duplicate amenity IDs, attempts to set host_id/status/removal metadata, empty patches, invalid timezone/coordinates, and explicit null for nonnullable fields return 422. Address line 2 and media captions can be cleared with null.

Money is returned as decimal strings, including `nightly_price`. Coordinates are JSON numbers; ZIP remains text. Cost ratings are derived: $ below 100, $$ below 200, $$$ below 300, $$$$ at least 300 USD/night.

Media URLs must use HTTPS without embedded credentials or whitespace. Media type is IMAGE or VIDEO; approval requires at least one IMAGE. Caption is optional, sort_order is nonnegative, and each listing supports at most 30 URLs. The backend stores URLs without fetching or uploading their content. Photos/order/caption changes count as material changes for reapproval.

Reference/request examples are in [listing form fixtures](fixtures/listings.json). Use real amenity IDs from `/host/amenities`; fixture IDs/timestamps must not be treated as actual created resources.

## Weekly hours and booking rules

PUT requests are full replacements with exactly seven unique entries, Monday=0 through Sunday=6. Times use listing-local `HH:MM`, including in responses. Overnight windows are unsupported.

- Contact hours body: `{"hours":[...]}`. Open days require opening_time < closing_time. Closed days omit both times. These hours are display information; changing them does not restrict accepted guest stays.
- Booking rule body: `{"booking_rules":[...]}`. Each enabled arrival/departure day needs start <= default <= end. Disabled days omit their associated times. Approval needs at least one enabled arrival day and departure day.
- Recommended defaults: arrival 15:00 within 15:00–22:00; departure 11:00 within 07:00–11:00.

Rules may change without reapproval, but changes cannot disable or narrow a window used by an accepted future/ongoing noncancelled stay. Changing only a default is allowed when the existing accepted time remains inside the allowed window. DST ambiguity for new reservation times will be handled by the Phase 5/6 availability/booking service; Phase 4 protects the UTC snapshots already accepted.

## Blocks, history, and status transitions

Block JSON contains start_date/end_date as YYYY-MM-DD and a nonblank reason. Ranges are half-open `[start_date, end_date)`. Reversed/equal dates fail validation. An overlap with any noncancelled reservation or existing block returns 409; adjacent ranges and cancelled reservation dates are allowed. Blocks are separate from weekly rules and have no AVAILABLE override.

Transitions:

- New listing → PENDING.
- Only a PENDING listing can be approved or rejected. Approval requires complete valid description/address/contact/coordinates/timezone, positive price/capacity, an HTTPS photo, and complete valid weekly hours/rules. Failure returns 422 LISTING_INCOMPLETE with field details and no audit action.
- A real name/location/description/capacity/amenity/photo change to APPROVED → PENDING. A no-op patch leaves approval unchanged. Other edits to REJECTED → PENDING.
- Price/contact/contact-hours/booking-rule/block changes preserve approval. Approved contact fields cannot be cleared to invalid/blank values.
- Location/timezone edits are rejected with 409 while future/ongoing stays depend on them. Capacity cannot drop below such a stay's guest count. Booking snapshots are not rewritten.
- Listing removal is terminal REMOVED. It hides the listing from future booking eligibility but retains all reservations/reviews and does not cancel stays. Later edits/moderation return 409. Owners/Admins can still read their authorized history.

Host DELETE, Admin DELETE, and Admin reject all require JSON `{"reason":"..."}`. Removal records actor, reason, and UTC timestamp in `listing_removals`. Admin decisions additionally use `admin_actions`; Host removal never masquerades as an Admin action. Repeated removal returns the original result without changing the reason or adding duplicate records.

The migration does not invent actors/reasons for unknown historical removals. Such legacy rows may have `removal=null`; explicit demo seed records are identified and populated separately. The API has no update/delete route for removal audit records.

## Isolation, errors, and verification

Every mutation acquires the listing row lock before reading child state or changing inventory. State is refreshed after waiting for another transaction. Parent/child ownership is checked on every nested ID. Future booking/cancellation services must use the same listing-first lock order; Phase 4 does not claim booking-versus-block races are complete before those APIs exist.

Expected errors: 401 missing/invalid bearer; 403 wrong role; 404 missing/foreign owned listing or nested child; 409 removed/state/future-stay/date conflict; 422 invalid fields, unknown amenities, missing reason, or incomplete approval. Errors use the common JSON envelope and request ID. All deletes return JSON, never 204.

```bash
make test TEST_PATH=tests/listings
make verify
make openapi
```

The PostgreSQL tests exercise the full Host/Admin lifecycle, ownership matrix, all nested operations, validation, audit atomicity/rollback, history protection, concurrent overlapping blocks, and a queued writer observing a committed removal. Shared React create → Admin approve → future Customer search acceptance is still pending; the public search endpoints arrive in Phase 5.

References: [SQLAlchemy SELECT locking](https://docs.sqlalchemy.org/en/20/core/selectable.html#sqlalchemy.sql.expression.Select.with_for_update), [Pydantic validation](https://docs.pydantic.dev/latest/concepts/validators/), [Python IANA timezones](https://docs.python.org/3.12/library/zoneinfo.html).
