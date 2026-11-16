# Public search, details, availability, and quotes

Phase 5 exposes approved rentals publicly and supplies a shared nightly/date/time validator for Phase 6. These endpoints require no bearer token. They do not create reservations, acquire inventory locks, call Google, or make a quote a guaranteed booking.

## Setup and quick checks

```bash
make setup
make db-up
make migrate
make seed
make api
```

No new schema migration is introduced by Phase 5. The current required head remains `0002_listing_removal_audit`. The pinned tzdata package supplies a fallback when the OS does not provide IANA timezone data; Python uses its normal system-first timezone lookup.

Open `http://127.0.0.1:8000/docs` and use the **public listings** group. No Authorize step is needed. In a second terminal:

```bash
curl -sS 'http://127.0.0.1:8000/api/v1/amenities'
curl -sS 'http://127.0.0.1:8000/api/v1/listings/search?city=San%20Jose'
curl -sS 'http://127.0.0.1:8000/api/v1/listings/search?check_in=2030-01-10&duration_nights=2&guests=2'
```

The example dates are illustrative future dates, not a promised availability result. Use a returned approved listing ID for detail and availability checks. For a real integration, derive dates from the user's selection instead of hardcoding examples.

## Routes

| Method/path | Query | Result |
|---|---|---|
| GET `/api/v1/amenities` | None | `success/data` array of amenity UUIDs and names |
| GET `/api/v1/listings/search` | Stay + search filters below | Approved cards, top-level pagination |
| GET `/api/v1/listings/{id}` | Optional stay fields | Approved detail, optionally with quote/availability |
| GET `/api/v1/listings/{id}/availability` | Required check_in plus check_out or duration_nights | Availability and indicative quote for one listing |

Pending, rejected, removed, and missing IDs return the same 404 for public detail/availability. Host/Admin routes remain separate and can show authorized management history. Static `/listings/search` is registered before the UUID route.

## Stay and filter contract

Dates are `YYYY-MM-DD`. Arrival/departure time inputs are listing-local `HH:MM`, without a timezone offset or seconds. Returned accepted UTC timestamps include an offset/Z; displayed local times remain HH:MM.

| Parameter | Rules |
|---|---|
| check_in | Omit to browse; otherwise supply check_out or duration_nights |
| check_out | Exclusive checkout date; local date difference must be 1–14 nights |
| duration_nights | Integer 1–14; if check_out is also supplied they must agree |
| check_in_time / check_out_time | Optional with dates; defaults come from that listing's check-in/check-out weekday rules |
| guests | Positive count; defaults to 1 for a stay. With browse, an explicit value still filters capacity |
| city | Trimmed case-insensitive exact city; no wildcard matching |
| state | Two-letter state, normalized to uppercase |
| zip_code | US ZIP text, five digits or ZIP+4; preserve leading zeroes |
| latitude / longitude / radius_km | Supply all three together; coordinates within ±90/±180 and radius >0 through 500 km |
| amenities | Repeated UUID query values from public reference amenities; every requested ID must match |
| min_price / max_price | Inclusive nonnegative USD nightly bounds, at most two decimals; min <= max |
| available_only | Defaults true with a valid stay, false when browsing. Explicit true without dates returns 422 |
| sort | newest (default), price_asc, price_desc, rating_desc, distance_asc; distance sort requires a coordinate/radius filter |
| page / page_size | page >=1; page_size 1–50, default 10 |

All supplied filters combine with **AND**. Repeated amenity IDs are rejected; a valid but unknown UUID produces no matches. For two amenities, encode `?amenities=<uuid1>&amenities=<uuid2>`, not a comma-separated string or amenity names. Unknown query properties are rejected.

Pagination is `{"success":true,"data":[...],"pagination":{"page":1,"page_size":10,"total_items":8,"total_pages":1}}`. Totals are computed after all filters, including availability/radius. Out-of-range pages return an empty array while preserving totals; no matches have total_pages=0. Ties use ascending UUIDs. Rating sort puts unrated listings last. Distance filtering/sorting uses full Haversine precision, with kilometers rounded to three decimals only for display.

## Browse versus selected stay

Without dates, cards/detail return `available=null`, `total_cost=null`, and `quote=null`. React may show the nightly price but must not show a confirmed total or enable Book.

With a valid stay, responses include an indicative quote: check_in/check_out, nights, guests, accepted check-in/check-out local times, accepted UTC arrival_at/departure_at, nightly_price, USD currency, and server-computed total_cost. Money is serialized as decimal strings. Nights are local date differences, never hours/24, including daylight-saving transitions. Unsupported totals beyond NUMERIC(10,2)'s monetary range are rejected rather than quoted as bookable.

Nightly inventory uses `[check_in, check_out)`. Back-to-back stays are allowed, while changing arrival/departure times cannot bypass occupied nights. Confirmed bookings and Host blocks consume inventory; cancelled bookings do not. With `available_only=false`, valid stays blocked by inventory remain in search with `available=false`, `unavailable_reason=DATES_UNAVAILABLE`, and an indicative quote. No booking/customer details are exposed.

Capacity and weekday/window/time eligibility always apply to dated search, even when available_only=false. A listing whose valid search time falls outside its window is excluded rather than offered an invalid quote. Display contact hours do not control stay eligibility.

## Validation and listing-local time

Malformed global parameters, inconsistent duration/dates, missing coordinate partners, invalid bounds, and explicit availability-only browse return JSON 422 with the standard error envelope/request ID. Dates before the current local date even in UTC-12 are rejected as globally past. For potentially current local dates, arrival must still be strictly in the future in the listing timezone; a UTC date comparison alone would reject valid western-timezone arrivals.

The shared validator roundtrips both folds through UTC. Ambiguous/nonexistent local timestamps are rejected instead of guessing a DST offset. In a multi-timezone search, only the affected listing is excluded; other matching timezones may remain. For a single listing's detail/availability, invalid local windows/capacity/past arrival/DST produce explicit 422 errors such as GUEST_LIMIT, OUTSIDE_BOOKING_WINDOW, ARRIVAL_IN_PAST, AMBIGUOUS_LOCAL_TIME, or NONEXISTENT_LOCAL_TIME, with field details.

Search and detail/availability use the same accepted stay data and inventory overlap helper. Phase 6 must re-read/validate under the existing listing-row lock and recheck inventory and price in the booking transaction. The current read-only quote is not that transaction.

## Public fields and privacy

Cards include name/address/city/state/ZIP, numeric coordinates, timezone, guest limit, all media/amenities, nightly price/currency/cost rating, average_rating, review_count, bookings_today, quote/availability, and optional distance_km. Detail additionally includes description, address line 2, Host-managed contact fields, all contact hours, and booking rules. Management-only Host IDs, moderation/audit/removal records, customer IDs/profiles, passwords, and reservation details are excluded by explicit public response models.

Average rating/count only include submitted reviews of noncancelled checked-out stays, with submission time not after the request clock. Listings with no eligible reviews have average_rating=null and review_count=0. `bookings_today` counts currently noncancelled bookings created during the full current local date in that listing's IANA timezone, rather than the UTC date. These are booking counts, not payments or revenue.

The implementation applies coarse database filters, bulk-loads child rows/aggregates, and evaluates timezone eligibility, radius, and pagination over matching candidates. This avoids N+1 queries and silent result truncation for the planned small demo dataset. A large production catalog would need database-oriented geospatial/search pagination work beyond this project phase.

## Frontend handoff and verification

Use [public search fixtures](fixtures/search.json), Swagger, and the reproducible local setup for React login → search → detail work. The fixtures contain illustrative IDs, dates, and totals; use live returned IDs and quotes for real requests. No Google API key is needed for these backend filters. Live Google address selection/map display remains Phase 9.

```bash
make test TEST_PATH=tests/search
make verify
make openapi
```

Tests cover each filter plus combinations, dates/duration/windows, 1/14-night boundaries, inventory conflicts/back-to-back/cancellation, DST, price/radius/rating ordering, pagination, leading-zero ZIPs, public privacy, and listing-local daily counts. Actual React flow acceptance and manual browser interaction remain pending teammate integration.

References: [Python timezone semantics](https://docs.python.org/3.12/library/zoneinfo.html), [FastAPI query models](https://fastapi.tiangolo.com/tutorial/query-param-models/), [tzdata fallback](https://pypi.org/project/tzdata/).
