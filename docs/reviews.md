# Reviews and ratings

Phase 7 adds Customer review creation and public listing reviews using the existing table/unique booking constraint. No new dependency or migration is required; Alembic head stays `0002_listing_removal_audit`.

## Local walkthrough

From the project root with Docker running:

```bash
make db-up
make api
```

Open `http://127.0.0.1:8000/docs` and the **reviews** group. Public review reads need no login. To post, log in at `/api/v1/auth/login` as a Customer (local demo: `customer1@example.test` / `DemoOnly!2026`), then Authorize with `data.access_token`.

1. GET `/api/v1/bookings/my` and select an owned COMPLETED booking. Copy its booking `id`, not its listing ID.
2. POST `/api/v1/reviews` with that actual UUID:

```json
{
  "booking_id": "11111111-1111-4111-8111-111111111111",
  "rating": 5,
  "comment": "A comfortable stay and a convenient location."
}
```

3. An eligible unreviewed stay returns 201. Repeat submission returns 409 REVIEW_ALREADY_EXISTS without editing the original.
4. GET `/api/v1/listings/{listing_id}/reviews` with the booking's listing ID. For an approved listing, the review appears and listing detail/search average_rating and review_count reflect it.
5. Future/ongoing/cancelled owned bookings give 409 REVIEW_NOT_ALLOWED; foreign/missing bookings give 404; bad rating/comment gives 422; unauthenticated posting gives 401.

**The original seed already reviews every eligible completed stay.** Posting for those IDs correctly returns 409. Automated tests prepare an unreviewed past stay only inside disposable test schemas and verify the 201 → public review → updated ratings workflow without editing development history. Successful manual UI/demo submission needs an owned, completed, unreviewed stay; preparation for that shared demo is pending. Do not rewrite accepted stay dates to bypass eligibility.

```bash
make test TEST_PATH=tests/reviews
make verify
make openapi
```

The first command tests reviews; verify runs lint, all backend tests, and schema drift checks. Both PostgreSQL services must be running, and the development schema must already be migrated. Tests migrate fresh UUID schemas in the separate test database.

## Contract

| Method/path | Input/access | Success |
|---|---|---|
| POST `/api/v1/reviews` | Customer bearer token; booking_id, rating, comment | 201 `success/data` with review ID, owned booking/listing IDs, rating, comment, created_at |
| GET `/api/v1/listings/{listing_id}/reviews` | Public; page >=1, page_size 1–50, default 10 | 200 safe review array with top-level pagination |

Rating is a strict JSON integer 1–5, rejecting strings, booleans, and fractional values. Comment is required plain text, trimmed, 1–2000 characters; Unicode, newlines, and tabs are allowed. NUL and other disallowed control characters are rejected before PostgreSQL. Unknown body/query fields are rejected. Clients cannot supply review/customer/listing IDs, submission time, or computed averages in the create body.

Creation requires the authenticated Customer's own booking with reservation_state=CONFIRMED and accepted UTC departure_at <= now. Eligibility opens exactly at checkout, matching computed COMPLETED; a local checkout date alone is insufficient. Cancelled stays remain ineligible. Public objects contain only id, rating, comment, created_at; no booking/customer/profile/contact data. The owner-only create response additionally includes their booking/listing IDs. Render comments as text.

Public pages require APPROVED listings; missing/pending/rejected/removed IDs share 404. Reviews and past-guest eligibility survive later removal/loss of approval, but public review pages stay hidden. A noncancelled checked-out guest may still leave their one review after removal without reopening/reapproving the listing.

## Pagination, aggregates, and transactions

Reviews sort by created_at descending then UUID ascending. Out-of-range pages, including very large positive page integers, return empty data while preserving totals; no reviews gives total_items=0 and total_pages=0.

Public pages and existing search/detail aggregates share a predicate: noncancelled booking, accepted checkout passed, and submitted timestamp not after the request clock. Invalid legacy/future/cancelled examples cannot inflate counts or ratings. Aggregates are queried, never manually edited/cached: no eligible reviews means average_rating=null and review_count=0. Averages round to two decimals, preserving the card contract.

Creation reads the owned parent ID, locks listing before booking, refreshes state, and reads the clock after waiting. PostgreSQL INSERT ON CONFLICT DO NOTHING RETURNING enforces the existing unique booking constraint. Concurrent duplicates yield one 201 and one safe 409. It commits once, rolls back failures, and preserves reservation snapshots and listing state. No review update/delete endpoints are introduced.

| HTTP/code | Meaning |
|---|---|
| 400 INVALID_JSON | Malformed JSON |
| 401 UNAUTHENTICATED / 403 FORBIDDEN | Invalid/missing token / wrong role |
| 404 NOT_FOUND | Missing/foreign booking or missing/nonpublic listing |
| 409 REVIEW_NOT_ALLOWED | Future, ongoing, or cancelled owned stay |
| 409 REVIEW_ALREADY_EXISTS | Review already exists; original retained |
| 422 VALIDATION_ERROR | Invalid fields/rating/comment/pagination |

Errors use the shared JSON envelope and matching X-Request-ID. See [JSON examples](fixtures/reviews.json) for React. Shared completed booking → submit → public reviews/updated ratings and browser acceptance remain pending; backend tests do not claim live UI acceptance. See the [phase audit](phase-acceptance.md) for earlier milestones and outstanding external checks.

References: [SQLAlchemy PostgreSQL conflict handling](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#insert-on-conflict-upsert), [PostgreSQL INSERT/RETURNING](https://www.postgresql.org/docs/16/sql-insert.html).
