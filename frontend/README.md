# Vacation Rental – React frontend

React (Vite) client for the FastAPI backend in `../backend`. It covers every implemented backend feature for the three roles.

## Run it

```bash
# 1. Start the backend first (from the repo root)
make setup && make db-up && make migrate && make seed && make api

# 2. Start the frontend
cd frontend
cp .env.example .env        # API URL; defaults to http://127.0.0.1:8000/api/v1
npm install
npm run dev                 # http://localhost:5173
```

The backend only allows the origins `http://localhost:5173` and `http://127.0.0.1:5173`, so Vite is pinned to port 5173 (`strictPort`). If you change the port, add the new origin to `CORS_ORIGINS` in `backend/.env`.

`VITE_API_BASE_URL` must include `/api/v1`; the app never appends it again.

Build for production: `npm run build` (output in `dist/`).

## Demo accounts (local seed data)

Password for all: `DemoOnly!2026`

| Role | Email |
|---|---|
| Customer | `customer1@example.test` (also 2, 3) |
| Host | `host1@example.test` (also host2) |
| Admin | `admin@example.test` |

In dev mode the login page has one-click buttons to fill these in.

## Screens and routes

| Route | Who | What |
|---|---|---|
| `/login`, `/register` | Public | JSON login; sign up as Customer or Host (Admin signup is not public) |
| `/` | Public | Search with city/state/ZIP, dates, guests, price, amenities, location radius, sorting, pagination |
| `/listings/:id` | Public | Gallery, details, hours/rules, reviews, availability check, quote and booking (Customers) |
| `/bookings`, `/bookings/:id` | Customer | History, confirmation, cancel before arrival, review completed stays |
| `/host` | Host | Analytics (30/60/90 days, ZIP filter), daily chart |
| `/host/listings` | Host | Own listings by status, soft-remove with reason |
| `/host/listings/new` | Host | Create listing with amenities, photo, weekly hours and rules |
| `/host/listings/:id` | Host | Edit details, photos, contact hours, booking rules, blocked dates |
| `/admin` | Admin | System analytics |
| `/admin/listings`, `/admin/listings/:id` | Admin | Pending queue / all listings, approve, reject and remove with reasons, full review page |
| `/admin/audit` | Admin | Moderation history, filter by listing |

## Structure

```
src/
  api/          client.js (fetch + envelope/error handling), endpoints.js (every backend route)
  context/      AuthContext (JWT in localStorage, /auth/me on load), ToastContext
  components/   Layout/navbar/RequireAuth, ui primitives, ListingCard, ListingForm, AnalyticsView
  pages/        public + customer pages; host/ and admin/ folders
  utils/        formatting, listing form <-> API payload helpers
```

## Notes

- Money and ZIP codes are strings; dates are `YYYY-MM-DD` in the listing's local timezone. Booking prices are always calculated by the server.
- A 401 on any signed-in request clears the session and sends the user to log in.
- **Maps use OpenStreetMap** (Leaflet + free OSM tiles; no API key, no billing): location map on each listing, results map on the search page, and address search with a draggable pin when hosts create or edit a listing. Address search uses OSM's free Nominatim service (press Enter or click Search; please keep usage light, it is meant for demos/coursework).
- Listing photos are HTTPS links (the backend stores URLs, it does not upload files).

## Frame-matched screens (latest update)

| Route | Screen |
|---|---|
| `/` | Search: search bar, filters, result rows, map with "Search as I move the map" |
| `/listings/:id` | Photo grid + lightbox, map, reviews (show more), live price quote |
| `/listings/:id/book` | Checkout / confirm booking, confirmation panel |
| `/bookings`, `/bookings/:id`, `/bookings/:id/review` | Upcoming / Past / Cancelled tabs, details, write a review |
| `/host/listings`, `/host/analytics` | Host listings and analytics |
| `/admin/listings` (pending queue with ZIP filter + sort), `/admin/analytics`, `/admin/audit` | Admin |

### Where the frames go beyond the backend
- Photo upload is URL-based (the API stores media URLs, not files).
- Reviewer names show as "Guest"; the API does not return reviewer identity.
- Admin ZIP filter and sort work on the loaded page only.
- Not yet restyled to the frames: the host 4-step wizard with drag-reorder photos (the existing tabbed listing editor is used), per-listing host analytics, CSV export, and the admin review page layout.
