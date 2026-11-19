# Vacation Rental App

This repository contains the Python/FastAPI backend and shared API documentation for a vacation-rental application. Customers can search/book/review rentals, Hosts manage their properties, and Admins moderate listings. PostgreSQL stores the data. The React frontend is owned by the frontend teammate and is not included in this checkout yet.

## Current status and team ownership

| Area | Status / responsibility |
|---|---|
| Backend APIs and local database | Phases 0–8 implemented and tested: auth, listings/moderation, search, bookings/cancellation, reviews and analytics |
| React screens and API client | Frontend owner; implementation/integration pending |
| Google address search and map | Frontend owner, with backend support; approved Google access and live integration pending |
| Integration testing | Shared; backend API tests in place, actual React/browser/Maps acceptance pending |
| Production packaging and Azure | Deployment owner; Docker images, nginx, scale set/load balancer/PostgreSQL deployed and tested on Azure (see [deployment guide](docs/deployment.md)) |

Start from `main` for the merged backend. Use a feature branch and pull request for changes. Coordinate where the teammate's existing React app will live rather than creating a second frontend. See the [phase audit](docs/phase-acceptance.md) for evidence and remaining checks.

Team/member names: `[PENDING: team name, backend owner, frontend owner]`. Task board and instructor burndown sheet: `[PENDING: links]`.

## Prerequisites

- Python 3.12 (required; `make setup` checks this)
- Docker Desktop or another Docker-compatible runtime with Compose, running before database commands
- GNU Make

The commands below use a Bash/Zsh-style shell on macOS/Linux or WSL. Frontend dependencies and commands will come from the teammate's actual React app.

## Clone the repository

```bash
git clone https://github.com/SuprithaMallaradhya/Vacation-Rental-App.git
cd Vacation-Rental-App
```

If you already cloned the repository, open its root folder and use the team's normal branch/update workflow. Run the following Make commands from that root.

## Local setup

```bash
if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
fi
make setup
make db-up
make migrate
make seed
```

Each teammate runs their own local database and seed; cloning Git does not copy another developer's database or environment file. The copy step above preserves an existing `backend/.env`. Keep real secrets in ignored environment files, and commit examples/placeholders only.

`make migrate` applies Alembic migrations. `make seed` inserts missing demo rows without updating or deleting existing data; a second run reports zero inserts. Neither command runs automatically at API startup.

If you already have a local `.env` from Phase 1, update its two database URLs to match the new ports in `backend/.env.example`. Ports 55432 and 55433 avoid conflicts with an existing PostgreSQL installation on 5432. The database services bind only to `127.0.0.1`.

## Run the API

```bash
make api
```

Leave that terminal running. In a second terminal, check:

```bash
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/ready
```

Open [Swagger](http://127.0.0.1:8000/docs) in a browser to try the APIs. ReDoc is at [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc).

`/health` is process-only and returns JSON 200 even when PostgreSQL is unavailable. `/ready` returns JSON 200 when PostgreSQL is reachable, all required tables exist, and its migration revision matches the application. It returns JSON 503 before migrations, for a stale schema, or during a database outage. Press Ctrl+C in the API terminal to stop the server.

## Frontend teammate: start here

| Setting / resource | Local value |
|---|---|
| Product API base URL | `http://127.0.0.1:8000/api/v1` |
| Swagger and request/response schemas | `http://127.0.0.1:8000/docs` |
| OpenAPI JSON | `http://127.0.0.1:8000/openapi.json` |
| Allowed React origins | `http://localhost:5173`, `http://127.0.0.1:5173` |
| Example payloads | [docs/fixtures](docs/fixtures) and the feature guides below |

Run the backend locally using the setup above. Log in through Swagger with a demo account, then try one authenticated request before wiring the React API client. Login is JSON; protected requests send `Authorization: Bearer <access_token>`. Ordinary successes use `success/data`, paginated lists also include top-level `pagination`, and errors include `error.code/message/details` plus `request_id`. Money and ZIP codes are strings. Read the [API contract](docs/api-contract.md) and [authentication handoff](docs/authentication.md) for exact formats.

Use the app's agreed environment variable for the API base URL; do not append `/api/v1` twice. If React uses another port, agree and configure that exact origin in `backend/.env` before starting the backend. The existing allowlist does not include arbitrary ports.

`localhost`/`127.0.0.1` refers to the machine making the request. A teammate cannot use your laptop's localhost URL from their computer: each person can run this local setup, or the team must explicitly arrange a shared development connection. No early Azure deployment is needed to start frontend integration.

## React frontend (`frontend/`)

### Overview

This directory contains the single-page web client for the Vacation Rental App (CMPE 202). The client consumes the REST API implemented in `backend/` (FastAPI, SQLAlchemy, PostgreSQL) and supports three roles: **Customers** search, book and review rentals; **Hosts** create and maintain listings and view analytics; **Administrators** moderate listings and view system analytics. The user interface follows the project's Whimsical wireframes ("Vacation Rental App: UI Wireframes (CMPE 202)", four frames: login/register/admin, host listings, search/maps/analytics, bookings/reviews), with a deliberately playful visual theme layered on top without changing any functionality.

### Technology stack

| Concern | Choice | Rationale |
|---|---|---|
| UI library | React 18 | Component model; no additional state library required |
| Build tool / dev server | Vite 5 | Fast start-up, native ES modules, pinned to port 5173 |
| Routing | react-router-dom 6 | Nested layouts, role-guarded routes, URL-encoded search state |
| HTTP | Browser `fetch` wrapped in `src/api/client.js` | Single place for auth headers, error normalisation and 401 handling |
| Maps | Leaflet 1.9 with OpenStreetMap tiles | No API key and no billing (see Design decisions) |
| Address search | OpenStreetMap Nominatim | Free geocoding; explicit user-triggered search only |
| Styling | Plain CSS (`src/styles.css`), Nunito web font | No CSS framework; theme defined with CSS custom properties |
| Charts | Hand-written SVG (`AnalyticsView.jsx`) | Avoids a charting dependency |

Runtime dependencies are limited to `react`, `react-dom`, `react-router-dom` and `leaflet`.

### System architecture and how the frontend is connected to the backend

```
Browser (React SPA, http://localhost:5173)
   │  fetch + JSON, header "Authorization: Bearer <JWT>"
   ▼
FastAPI backend (http://127.0.0.1:8000/api/v1)   ← CORS allow-list: localhost:5173, 127.0.0.1:5173
   │  SQLAlchemy (async) + Alembic migrations
   ▼
PostgreSQL 16 in Docker (127.0.0.1:55432, database vacation_rental_dev)
```

**Transport and base URL.** All requests go through `src/api/client.js`. The base URL is read from `VITE_API_BASE_URL` (default `http://127.0.0.1:8000/api/v1`) and must already include `/api/v1`; the client never appends it again. Every backend route is wrapped once in `src/api/endpoints.js`, grouped as `auth`, `publicApi`, `bookingsApi`, `reviewsApi`, `hostApi` and `adminApi`; pages never construct URLs themselves.

**CORS.** The backend permits only `http://localhost:5173` and `http://127.0.0.1:5173`. Consequently the Vite dev server is pinned to port 5173 with `strictPort: true` (`vite.config.js`); it fails rather than silently choosing another port. Using a different origin requires adding it to `CORS_ORIGINS` in `backend/.env`.

**Authentication.** `POST /auth/login` accepts JSON and returns a JWT access token and the user record. The token is stored by `tokenStore`: in `localStorage` when "Remember me" is checked (persists after the browser closes) and in `sessionStorage` otherwise (current tab only). Each authenticated request sends `Authorization: Bearer <token>`. On application start, `AuthContext` calls `GET /auth/me` to restore the session. Any `401` response to an authenticated request clears the token and returns the user to the logged-out state. Route guards (`RequireAuth`) restrict pages by role (`CUSTOMER`, `HOST`, `ADMIN`); the backend independently enforces authorisation, so the client-side guards are a usability measure, not a security boundary.

**Response envelopes.** Successful responses have the shape `{ success, data }`; lists additionally contain `pagination { page, page_size, total_items, total_pages }`. Errors have the shape `{ success:false, error:{ code, message, details[] }, request_id }`. The client converts errors into an `ApiError` (status, code, message, details, request id, retry-after) and maps network failures to a `NETWORK_ERROR` with an actionable message. Field-level `details` are surfaced next to the corresponding form inputs (`fieldErrors`).

**Data conventions honoured by the client.** Monetary amounts and ZIP codes are handled as strings; stays are limited to 1–14 nights; dates are `YYYY-MM-DD` in the listing's local time zone; booking totals are always computed by the server and the client only displays them.

### Prerequisites

- Node.js 18 or later with npm
- Python 3.12, GNU Make, and Docker Desktop (running) for the backend
- A modern browser

### Installation and execution (commands)

All commands assume a macOS/Linux shell. Backend commands are run from the **repository root**; frontend commands from `frontend/`. The backend steps repeat "Local setup" and "Run the API" above and are listed so that this section is self-contained.

#### Backend and database (Docker)

```bash
# one-time
cp backend/.env.example backend/.env     # only if backend/.env does not yet exist
make setup                                # creates backend/.venv, installs dependencies

# every session
make db-up                                # docker compose up -d --wait postgres-dev postgres-test
make migrate                              # Alembic: alembic upgrade head
make seed                                 # inserts demo data (idempotent)
make api                                  # uvicorn on http://127.0.0.1:8000 (keep this terminal open)
```

Docker (`compose.yaml`) runs two PostgreSQL 16 containers with named volumes: `postgres-dev` on `127.0.0.1:55432` (database `vacation_rental_dev`) and `postgres-test` on `127.0.0.1:55433` (database `vacation_rental_test`, used only by the automated tests). Both use the user and password `vacation` and are bound to the loopback interface only. Docker Desktop must be running before `make db-up`; otherwise Docker reports that it cannot connect to the daemon. `make db-down` stops the containers while preserving data. Health checks: `http://127.0.0.1:8000/health` and `/ready`; interactive API documentation: `http://127.0.0.1:8000/docs`.

#### Frontend

```bash
cd frontend
cp .env.example .env     # defines VITE_API_BASE_URL
npm install
npm run dev              # http://localhost:5173
```

| Command | Purpose |
|---|---|
| `npm run dev` | Development server with hot reload on port 5173 |
| `npm run build` | Production bundle in `dist/` |
| `npm run preview` | Serves the production bundle on port 5173 |

The `.env` file is excluded from version control (`.gitignore`); only `.env.example` is committed. The only variable is `VITE_API_BASE_URL`. Vite reads environment files at start-up, so the dev server must be restarted after editing `.env`.

#### Demo accounts

The seed creates one administrator, two hosts and three customers. The shared development password is `DemoOnly!2026`.

| Role | Accounts |
|---|---|
| Customer | `customer1@example.test`, `customer2@example.test`, `customer3@example.test` |
| Host | `host1@example.test`, `host2@example.test` |
| Admin | `admin@example.test` |

In development builds the login page offers buttons that fill in these credentials. New Customer and Host accounts can be registered in the interface; administrator accounts cannot be self-registered.

#### Verifying that a booking reached the database

Via Swagger (`/docs`): log in, press **Authorize** with the access token, then call `GET /api/v1/bookings/my`. Directly in PostgreSQL:

```bash
docker compose exec postgres-dev psql -U vacation -d vacation_rental_dev
SELECT * FROM bookings ORDER BY created_at DESC LIMIT 5;
```

### Features by role

#### Shared and public

- **Authentication:** login with optional "Remember me"; registration with a Customer/Host selector (preselectable through `/register?role=host`), client-side validation (name, e-mail, phone, password of 8–72 bytes containing a letter and a digit, acceptance of the terms) combined with server validation messages that include the HTTP status.
- **Role-based navigation:** the navigation bar and the post-login landing page depend on the role; an avatar menu shows name, e-mail, role and log-out.
- **Search (`/`):** a free-text "Where" field (city, "City, ST", ZIP code), check-in/check-out dates (1–14 nights), guests, price range, amenities, a radius around a searched place or the user's location, sorting (top rated, newest, price, distance), an "available only" filter, and pagination. All search state is stored in the URL, so results are shareable and survive reload.
- **Result presentation:** rows with cover photo, location, capacity, amenities, average rating, review count, a "booked N times today" indicator, nightly price and, when dates are given, the total cost. A sticky map shows the result pins; the option "Search as I move the map" re-queries the backend using the visible map centre and a radius derived from the viewport.
- **Listing page (`/listings/:id`):** photo grid with a keyboard-navigable lightbox, description, amenities, weekly arrival/departure windows and host contact hours, map with an external OpenStreetMap link, paginated reviews with "Show more", and a booking card that obtains an automatic availability and price quote as soon as valid dates and guests are entered.

#### Customer

- **Checkout (`/listings/:id/book`):** summary of dates, times, guests and server-quoted total; mandatory acceptance of the house rules; server errors displayed with their status code; a confirmation panel with map, link to "My bookings" and cancellation.
- **My bookings (`/bookings`):** tabs for Upcoming, Past and Cancelled with counts and cover thumbnails; cancellation with confirmation (permitted only before the arrival time, as determined by the backend's `can_cancel`).
- **Booking detail (`/bookings/:id`)** and **review page (`/bookings/:id/review`):** a 1–5 star rating and a comment of up to 1000 characters (the API limit is 2000) for completed stays.

#### Host

- **My listings (`/host/listings`):** listings filtered by status (Pending, Approved, Rejected, Removed), edit, public page link, removal with a mandatory reason (soft removal; bookings and reviews are retained).
- **Listing editor (`/host/listings/new`, `/host/listings/:id`):** details with an OpenStreetMap address search that fills address fields and a draggable map pin that sets latitude and longitude; amenities; photo and video links; seven-day contact hours; seven-day booking (arrival/departure) rules; blocked dates. Material edits to an approved listing, or any edit to a rejected listing, return it to Pending as defined by the backend.
- **Analytics (`/host/analytics`):** 30/60/90-day windows, ZIP filter, summary tiles and a daily created/cancelled bookings chart.

#### Administrator

- **Listing moderation (`/admin/listings`):** pending queue (default) and filters for all/approved/rejected/removed; pending counter; ZIP prefix filter and sorting applied to the loaded page; approve with confirmation, reject or remove with a mandatory reason.
- **Review page (`/admin/listings/:id`):** complete listing information for decision making.
- **Analytics (`/admin/analytics`)** and **audit log (`/admin/audit`):** system-wide metrics and the history of moderation actions, filterable by listing.

### Design decisions

1. **OpenStreetMap instead of Google Maps.** Google Maps was first implemented (JavaScript API, Places API (New), advanced markers) and then replaced at the project owner's request, because Google's APIs require a billing-enabled key whose use must follow an approved course arrangement. Leaflet with OpenStreetMap tiles needs neither key nor billing. Address lookup uses Nominatim, whose usage policy prohibits search-as-you-type and requires modest request rates; the interface therefore searches only on Enter or on pressing **Search**, and attribution is displayed on every map. These services are appropriate for coursework and demonstrations; a production deployment should use a commercial or self-hosted tile and geocoding service.
2. **No state-management library.** Server data is fetched with a small `useAsync` hook that keeps previous data while reloading; authentication and notifications use React context.
3. **Single API layer.** `client.js` and `endpoints.js` centralise headers, error handling and routes, which keeps pages free of transport details and makes backend changes local.
4. **URL as the source of truth for search.** Filters, sorting, pagination and map position are stored in query parameters.
5. **Safe rendering.** User-supplied text is rendered through React or `textContent` (including map popups), never through `innerHTML`.
6. **Accessibility.** Labelled form controls, keyboard-operable dialogs and lightbox, ARIA roles on tabs and regions, and suppression of animation under `prefers-reduced-motion`.

### Visual theme

The wireframes were implemented first with a restrained blue palette and then given a playful theme requested by the project owner: warm background gradients, coral/yellow/mint/sky/purple accents, a rainbow rule beneath the navigation bar, gradient pill buttons, colour-coded amenity chips and result cards, an illustrated search banner, emoji accents and a confetti animation on booking confirmation. The theme is expressed entirely in CSS custom properties and the appended "Fun makeover" section of `styles.css`, so it can be removed or recoloured without touching component logic.

### Adaptations required by differences between the wireframes and the backend

| Wireframe element | Implementation | Reason |
|---|---|---|
| Photo upload with drag-and-drop | Photos and videos are added as URLs | The API stores media URLs and has no file-upload endpoint |
| "Draft" listing status | Not shown as a separate status | Backend statuses are PENDING, APPROVED, REJECTED, REMOVED |
| Host name in the admin queue | Not shown | The admin listing payload does not contain it |
| Rejection reason shown to hosts | Not shown | Not returned by the host API |
| Reviewer names | Displayed as "Guest" | The review payload carries no reviewer identity |
| Revenue in analytics | Labelled as booking value | The API reports booking totals, not payments |
| Admin ZIP filter and sort | Applied client-side to the current page | No server-side parameters exist |

### Known limitations and status

- **Verification performed:** the production build (`npm run build`) succeeds, and the search page and key components were rendered in a headless browser against mocked API responses. A complete end-to-end acceptance test of every flow against the live backend has not been recorded and should be carried out by the team before submission.
- **Not yet restyled to the wireframes:** the host four-step creation wizard with drag-to-reorder photos (the existing tabbed editor provides equivalent functionality), per-listing host analytics, CSV export of analytics, and the wireframe layout of the admin review page.
- No automated frontend tests are included.
- The OpenStreetMap services are subject to fair-use limits (see Design decisions).

### Project structure

```
frontend/
  index.html, vite.config.js, package.json, .env.example
  src/
    main.jsx, App.jsx           entry point and route table
    api/                        client.js (fetch, tokens, errors), endpoints.js (all routes)
    context/                    AuthContext (session, roles), ToastContext (notifications)
    hooks/                      useAsync, useQuote (availability + price), useCovers (thumbnails)
    lib/maps.js                 OpenStreetMap link and Nominatim search/parsing
    utils/                      format.js (dates, money, errors), listingForm.js (form <-> payload)
    components/                 Layout (navbar, guards), ui (shared widgets), MapView (Leaflet),
                                PlaceSearch, ListingForm, AnalyticsView
    pages/                      Login, Register, Search, ListingDetail, Checkout, MyBookings,
                                BookingDetail, ReviewPage, host/*, admin/*
    styles.css                  theme variables, components, "Fun makeover" section
```

### Troubleshooting

| Symptom | Cause and remedy |
|---|---|
| "Cannot connect to the Docker daemon" on `make db-up` | Start Docker Desktop and retry |
| "Cannot reach the server" in the browser | Backend not running: `make api`; check `VITE_API_BASE_URL` |
| Browser console CORS error | The page is not served from `localhost:5173` or `127.0.0.1:5173` |
| "Port 5173 is already in use" | Stop the earlier dev server, or free the port: `lsof -nP -iTCP:5173 -sTCP:LISTEN`, then `kill <PID>` |
| `.env` missing after replacing the folder | `cp .env.example .env` inside `frontend/`, then restart `npm run dev` |
| Terminal reports `No such file or directory` after replacing a folder | The terminal still points at the deleted folder; open a new terminal |
| "Email is already registered" | The address exists (for example a seeded demo account); log in or use another address |
| "Invalid email or password (401)" | No such account yet: register first |
| Placeholder text instead of photos | Seed images come from `placehold.co`; use real HTTPS image URLs for real listings |
| Empty results | Run `make migrate` and `make seed`; relax filters |

## Verification

```bash
make verify
```

`make verify` runs lint, all tests, and model/migration drift checks. Both database services must be running and the development database must be migrated. CI runs lint and tests with a separate PostgreSQL service; it does not deploy anything.

For a targeted check instead of the full gate, choose a test area such as `make test TEST_PATH=tests/auth`. `make lint` runs only the linter. `make openapi` exports `docs/openapi.json` for sharing; that generated file is ignored by Git.

| Purpose | Address | Database |
|---|---|---|
| Development | `127.0.0.1:55432` | `vacation_rental_dev` |
| Tests | `127.0.0.1:55433` | `vacation_rental_test` |

Tests require a local `TEST_DATABASE_URL` naming a separate database ending in `_test`. The test harness assigns the application to that URL before importing its engine. Each database test migrates a fresh `test_<uuid>` schema and removes only that schema afterward. It does not truncate development tables, reset databases, or delete volumes. A failed test connection fails the suite instead of silently skipping database tests.

When finished, `make db-down` stops the containers and preserves both volumes. No reset or volume deletion runs during setup, migrations, seed, or tests.

## Demo data

The dataset contains 1 Admin, 2 Hosts, 3 Customers, 12 listings across 4 ZIP codes, 18 bookings, and 7 eligible past-stay reviews. It also contains all listing states, varied prices/capacities, weekly hours/windows, photos, amenities, date blocks, cancellations, and moderation records. Booking creation timestamps cover the exact 30/60/90-day analytics boundaries and one microsecond on each side, relative to the initial seed time.

| Role | Local demo accounts |
|---|---|
| Customer | `customer1@example.test`, `customer2@example.test`, `customer3@example.test` |
| Host | `host1@example.test`, `host2@example.test` |
| Admin | `admin@example.test` |

All use the deliberately public local demo password `DemoOnly!2026`, stored only as bcrypt hashes in the database. Log in through `POST /api/v1/auth/login` using JSON. These are fictional development credentials, not deployment credentials.

The seed CLI refuses cloud/test/production targets and only permits `APP_ENV=development` with the local `vacation_rental_dev` database. The seed uses an anchored timeline; reruns preserve user edits and existing dates. To obtain a newer timeline later, use a separately approved local data-refresh procedure rather than silently resetting data.

## Authentication

Use `/api/v1/auth/register/customer` or `/api/v1/auth/register/host` with name, email, phone, and password. Roles are assigned by the server; Admin signup is not public. Login uses JSON email/password and returns an access token plus the safe user record inside `data`. In Swagger, submit the login example, click **Authorize**, paste `data.access_token`, then call `/api/v1/auth/me`.

Access tokens expire after 60 minutes by default. A blank `JWT_SECRET_KEY` generates a random process key in development/test, so restart/reload invalidates tokens. To keep local tokens across restarts, generate a secret and store it only in the ignored `.env`; an explicit secret of at least 32 bytes is mandatory outside development/test. Do not reuse the older example placeholder.

The basic process-local login limit is 10 attempts per client IP per 60 seconds. Login may return 429 with Retry-After; it is not a distributed limit across future VMs. See the [auth contract and React handoff](docs/authentication.md) for exact request/response examples, validation, 401/403 handling, and deployment limitations.

## Host listings and Admin moderation

After updating, run `make migrate` and `make seed`. Revision `0002_listing_removal_audit` adds removal history without changing existing listings/bookings. Hosts can create/edit their own pending listings, maintain media/amenities/contact hours/booking rules/date blocks, and soft-remove listings with a reason. Admins can review pending listings, approve/reject them, remove them with an audit record, and view moderation history.

Use the Host/Admin groups in Swagger with the appropriate demo token. Start with `GET /api/v1/host/amenities` for reference IDs. Complete listing details, a photo, and all seven weekdays of hours/rules before approval. Material edits require reapproval; future accepted stays protect their location, capacity, and booking windows. All DELETE endpoints return JSON, and listing removal requires a JSON reason. Read the [listing management contract](docs/listing-management.md) and [form examples](docs/fixtures/listings.json) before connecting React.

## Public search

Public endpoints now include `/api/v1/amenities`, `/api/v1/listings/search`, `/api/v1/listings/{id}`, and `/api/v1/listings/{id}/availability`. Browse without dates returns null quote/availability. Supply check_in plus check_out or duration_nights for 1–14-night quotes. Only approved listings are public; quotes do not reserve inventory. See the [public search contract](docs/public-search.md) for filters, timezone/DST rules, mock fixtures, and frontend integration. Existing checkouts should run `make setup` to install the timezone-data fallback dependency; no new migration is required.

## Customer bookings

Log in as a Customer and use the **customer bookings** Swagger group. POST `/api/v1/bookings` accepts a listing ID and the selected stay, calculates the current total on the server, and reserves available nights in a transaction. GET `/api/v1/bookings/my` lists your saved history; GET `/api/v1/bookings/{id}` shows your confirmation. PATCH `/api/v1/bookings/{id}/cancel` takes no body and cancels your future stay before arrival. Repeated cancellation preserves the original result. Details/prices survive listing edits/removal; completion is computed after checkout. See the [walkthrough and contract](docs/bookings.md) and [JSON examples](docs/fixtures/bookings.json). Phase 6 requires no new migration or dependency.

## Reviews and ratings

Customers can POST `/api/v1/reviews` with an owned noncancelled checked-out booking ID, integer rating 1–5, and a comment. Each booking can be reviewed once. GET `/api/v1/listings/{id}/reviews` publicly lists eligible reviews for an approved listing; search/detail rating aggregates update from the same eligibility rules. The original seed's eligible completed stays already have reviews, so duplicate rejection is expected for those IDs. See the [review walkthrough](docs/reviews.md), [JSON examples](docs/fixtures/reviews.json), and [phase audit](docs/phase-acceptance.md). No new migration or dependency is required.

## Host and Admin analytics

Use GET `/api/v1/host/analytics` with a Host token or GET `/api/v1/admin/analytics` with an Admin token. Both accept period_days=30/60/90 (default 30) and optional zip_code, and return current inventory/status counts, new listings, booking/cancellation/net counts, saved booking value, ZIP breakdowns, and UTC daily buckets. Host scope comes from auth. Booking value uses saved noncancelled totals and is not paid revenue. ZIPs use current listings versus saved booking ZIPs. See the [analytics walkthrough and metric/chart definitions](docs/analytics.md) and [JSON examples](docs/fixtures/analytics.json). No new migration or dependency is required.

## React and Google Maps integration status

The frontend teammate will connect the existing React app to these APIs and add Google address selection/map display. The backend already accepts latitude, longitude and radius_km for rental searches and returns listing coordinates. Google access and live React/browser acceptance remain pending; no Google key is required to test the backend's existing coordinate filters.

Agree on the API contract, origin/base URL and approved Google access before integrating the screens. Use the existing API guides and mock JSON examples to work in parallel. Backend tests and Swagger checks do not prove that a React screen or live map works. See the [external-check register](docs/external-checks.md) for pending access and team details.

## Project constraints and remaining work

Finish the teammate's React screens/client and Google Maps integration, verify complete Customer/Host/Admin flows together, then complete production packaging, budget-gated Azure deployment, and final demo/documentation/process evidence. Backend API tests do not establish that the UI or deployment works.

- Deadline: **December 2, 2026, 11:59 PM**; `[PENDING: course timezone and Demo Day/evaluation window]`.
- Azure student-credit limit: **$10 total across the project**, targeting $7 usage plus $3 reserve. No personal payment, Pay-As-You-Go upgrade, or additional paid subscriptions.
- Google Maps access/billing is separate from Azure. Use an approved course/institutional arrangement consistent with the no-personal-payment rule; live access remains pending. See the [external-check register](docs/external-checks.md).
- Develop and test locally first. This README does not authorize cloud provisioning or paid-service activation.

## Project documents

- [Implementation status](docs/implementation-status.md)
- [Design decisions](docs/design-decisions.md)
- [Design patterns and code smells](docs/design-patterns.md)
- [Media storage and uploads](docs/media-storage.md)
- [API contract](docs/api-contract.md)
- [Authentication and frontend handoff](docs/authentication.md)
- [Host listings and Admin moderation](docs/listing-management.md)
- [Public search, availability, and quotes](docs/public-search.md)
- [Customer bookings, history, and cancellation](docs/bookings.md)
- [Reviews and ratings](docs/reviews.md)
- [Host and Admin analytics](docs/analytics.md)
- [Backend phase acceptance audit](docs/phase-acceptance.md)
- [Requirement coverage](docs/requirement-coverage.md)
- [Product backlog](docs/product-backlog.md)
- [External checks](docs/external-checks.md)
- [Backend design V2](BACKEND_PLAN_AND_DESIGN_V2.md)
- [Database schema and ERD](docs/database.md)
