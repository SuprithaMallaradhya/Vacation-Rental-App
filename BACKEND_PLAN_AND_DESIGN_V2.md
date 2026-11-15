# Vacation Rental Application

## Backend Plan and Design Document — Version 2

**Deadline:** December 2, 2026 at 11:59 PM\
**Backend owner:** [Your Name]\
**Frontend owner:** [Teammate Name]\
**Status:** Revised draft for team approval\
**Supersedes:** BACKEND_PLAN_AND_DESIGN.md

### Confirmed project decisions — November 15, 2026

- Use Version 2 as the main readable plan and retain its architecture diagrams.
- Stack: FastAPI, React, PostgreSQL, SQLAlchemy, Alembic, and JWT role-based authorization.
- Develop and test locally before provisioning Azure.
- Maximum total Azure student-credit use: **$10 for the entire project**, including November and December. Target operating usage below $7 and reserve $3 for delayed charges. These are planning limits; Azure alerts cannot enforce a hard $10 cutoff.
- No personal payment or Pay-As-You-Go upgrade. Verify actual eligibility and the complete estimate before deployment; zero credit usage is not guaranteed.
- Model rentals as **1–14 nightly stays**, with listing-local check-in/check-out times and windows. Times do not permit two reservations for the same night.
- You own backend/deployment and contribute to integration; your teammate owns React/UI. Both contribute to testing, documentation, Scrum evidence, and the demo.
- Preserve the essential V3 technical corrections when implementing: derived completion after checkout, cancellation/history rules, defined analytics, host availability operations, actual Google address search, and HTTPS/outbound networking.
- Keep deployment available for the actual instructor evaluation window, then export evidence/data and remove project resources.

---

## Contents

1. Project goal
2. Technology stack
3. Scope and roles
4. Architecture
5. Backend structure
6. Database design
7. API design
8. Business rules
9. Authentication and security
10. Google Maps
11. Cost-controlled Azure deployment
12. Testing and mock data
13. Team responsibilities
14. Agile artifacts
15. Sprint schedule
16. Integration plan
17. Demo plan
18. Definition of done
19. Final checklist
20. Approval decisions

---

## 1. Project Goal

Build an end-to-end vacation rental application similar to Airbnb.

| Role | Capabilities |
|---|---|
| Customer | Search, view, book, cancel, review, and rate rentals |
| Host | Create, update, remove, and analyze personal listings |
| Admin | Approve, reject, remove listings, and view system analytics |

The backend will expose versioned JSON REST APIs consumed by the React frontend.

### Required outcomes

- Working backend APIs
- React web UI calling the APIs
- PostgreSQL database with realistic mock data
- Customer, Host, and Admin roles
- Input validation and JSON error handling
- Cloud deployment with autoscaled virtual machines and a load balancer
- Component, deployment, and database diagrams
- UI wireframes
- GitHub project journal
- Product backlog, sprint backlogs, task board, and burndown chart
- README with design decisions and contribution summary
- Working demo
- Evidence of contributions from every team member

---

## 2. Technology Stack

| Area | Technology |
|---|---|
| Backend | Python 3.12+ and FastAPI |
| Validation | Pydantic |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Database | PostgreSQL |
| Authentication | JWT and bcrypt |
| API documentation | FastAPI Swagger/OpenAPI |
| Testing | Pytest and HTTPX |
| Frontend | React |
| Maps | Google Maps, added after core APIs work |
| Containers | Docker |
| Cloud | Azure for Students |

### Cloud mapping

| Project requirement | Azure service |
|---|---|
| EC2-equivalent autoscaled cluster | Azure Virtual Machine Scale Set |
| Load balancer | Azure Load Balancer |
| Managed database | Azure Database for PostgreSQL Flexible Server |
| Monitoring | Azure Monitor, only if within free allowance |

---

## 3. Scope and Roles

### Customer features

- Register and log in.
- Search rentals by:
  - Check-in and check-out dates
  - Start and end time
  - Number of guests
  - Duration
  - Availability
  - City and state
  - ZIP code
  - Location coordinates or map search
- View listing details.
- View photos and/or videos.
- View amenities.
- View cost per night, total cost, and cost rating.
- View ratings, reviews, and average rating.
- View number of bookings today.
- View listing location on a map.
- Book a stay.
- Cancel a booking.
- View booking history.
- Review and rate a past booking.

### Host features

- Register and log in.
- Add a listing.
- View personal listings.
- Update a listing.
- Remove a listing using soft deletion.
- Maintain:
  - Name
  - Address
  - City, state, and ZIP code
  - Contact information
  - Hours
  - Available booking times
  - Maximum guests
  - Description
  - Photos and/or videos
  - Amenities
  - Cost per night
  - Cost rating
- View analytics for personal listings.
- Filter analytics by 30, 60, and 90 days.
- View bookings grouped by ZIP code.

### Admin features

- Log in.
- View pending listings.
- Approve new listings.
- Reject incomplete or inaccurate listings.
- Remove listings using soft deletion.
- View system-wide analytics.
- Filter analytics by 30, 60, and 90 days.
- View bookings grouped by ZIP code.
- View an audit trail of listing decisions.

---

## 4. Architecture

~~~mermaid
flowchart TD
    Browser[Customer / Host / Admin Browser]
    Frontend[React Frontend]
    LB[Azure Load Balancer]
    VMSS[Azure Virtual Machine Scale Set]
    API1[FastAPI Instance 1]
    API2[FastAPI Instance 2]
    DB[(Azure PostgreSQL)]
    Maps[Google Maps API]

    Browser --> Frontend
    Frontend --> LB
    LB --> VMSS
    VMSS --> API1
    VMSS --> API2
    API1 --> DB
    API2 --> DB
    Frontend --> Maps
~~~

### Architecture principles

- API servers are stateless.
- PostgreSQL is the shared source of truth.
- JWT allows requests to reach any API instance.
- Media is represented by URLs to avoid cloud storage costs.
- Listing coordinates are stored in the database.
- All application timestamps are stored in UTC.
- Local development is completed before cloud deployment.
- API version one is used for all public routes.

### Component diagram

~~~mermaid
flowchart TD
    Routers[FastAPI Routers]
    Validation[Pydantic Validation]
    Auth[Authentication Service]
    Listings[Listing Service]
    Bookings[Booking Service]
    Reviews[Review Service]
    Analytics[Analytics Service]
    Audit[Admin Audit Service]
    Data[SQLAlchemy Data Layer]
    PostgreSQL[(PostgreSQL)]

    Routers --> Validation
    Routers --> Auth
    Routers --> Listings
    Routers --> Bookings
    Routers --> Reviews
    Routers --> Analytics
    Routers --> Audit
    Auth --> Data
    Listings --> Data
    Bookings --> Data
    Reviews --> Data
    Analytics --> Data
    Audit --> Data
    Data --> PostgreSQL
~~~

### Deployment diagram

~~~mermaid
flowchart TD
    User[Web Browser]
    React[React Frontend]
    ALB[Azure Load Balancer]
    VMSS[Azure VM Scale Set]
    VM1[FastAPI VM 1]
    VM2[FastAPI VM 2]
    DB[Azure PostgreSQL Flexible Server]
    Monitor[Azure Monitor]

    User --> React
    React --> ALB
    ALB --> VMSS
    VMSS --> VM1
    VMSS --> VM2
    VM1 --> DB
    VM2 --> DB
    VM1 --> Monitor
    VM2 --> Monitor
~~~

---

## 5. Backend Structure

~~~text
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── dependencies.py
│   ├── database/
│   │   ├── session.py
│   │   └── base.py
│   ├── models/
│   ├── schemas/
│   ├── routers/
│   │   ├── auth.py
│   │   ├── listings.py
│   │   ├── bookings.py
│   │   ├── reviews.py
│   │   ├── host.py
│   │   └── admin.py
│   ├── services/
│   │   ├── availability_service.py
│   │   ├── booking_service.py
│   │   └── analytics_service.py
│   └── middleware/
│       └── error_handler.py
├── alembic/
├── tests/
├── seed/
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── .env.example
└── README.md
~~~

| Module | Responsibility |
|---|---|
| auth | Registration, login, JWT, and roles |
| listings | Search, details, Host CRUD, and Admin approval |
| bookings | Availability, booking, cancellation, and overlap protection |
| reviews | Ratings and comments |
| analytics | Host and Admin dashboards |
| audit | Admin approval, rejection, and removal history |
| database | Sessions, transactions, migrations, and indexes |
| middleware | Errors, logging, CORS, and request IDs |

---

## 6. Database Design

### Users

~~~text
users
- id
- name
- email                         UNIQUE
- password_hash
- phone
- role                          CUSTOMER, HOST, ADMIN
- timezone                      default America/Los_Angeles
- created_at                    UTC
- updated_at                    UTC
~~~

### Listings

~~~text
listings
- id
- host_id                       FK users.id
- name
- description
- address
- city
- state
- zip_code
- latitude
- longitude
- contact_info
- cost_per_night
- cost_rating                   $, $$, $$$, $$$$
- max_guests
- status                        PENDING, APPROVED, REJECTED, REMOVED
- created_at                    UTC
- updated_at                    UTC
- removed_at                    nullable
~~~

Cost rating rules for seeded data:

~~~text
$       under $100 per night
$$      $100 to $199 per night
$$$     $200 to $299 per night
$$$$    $300 or more per night
~~~

### Listing hours

~~~text
listing_hours
- id
- listing_id                    FK listings.id
- day_of_week                   MONDAY through SUNDAY
- opening_time
- closing_time
~~~

### Available booking times

~~~text
listing_booking_windows
- id
- listing_id                    FK listings.id
- day_of_week
- start_time
- end_time
~~~

### Listing media

~~~text
listing_media
- id
- listing_id                    FK listings.id
- url
- media_type                    IMAGE or VIDEO
- caption
~~~

### Amenities

~~~text
amenities
- id
- name                          UNIQUE

listing_amenities
- listing_id                    FK listings.id
- amenity_id                    FK amenities.id
~~~

### Availability blocks

~~~text
availability_blocks
- id
- listing_id                    FK listings.id
- start_datetime                UTC
- end_datetime                  UTC
- status                        AVAILABLE or BLOCKED
- reason
~~~

### Bookings

~~~text
bookings
- id
- listing_id                    FK listings.id
- customer_id                   FK users.id
- check_in                     date
- check_out                    date
- start_time                   nullable
- end_time                     nullable
- guests
- total_cost
- status                        CONFIRMED, CANCELLED, COMPLETED
- created_at                    UTC
- updated_at                    UTC
- cancelled_at                  nullable
~~~

### Reviews

~~~text
reviews
- id
- listing_id                    FK listings.id
- customer_id                   FK users.id
- booking_id                    FK bookings.id UNIQUE
- rating                        1 through 5
- comment
- created_at                    UTC
~~~

### Admin audit actions

~~~text
admin_actions
- id
- admin_id                      FK users.id
- listing_id                    FK listings.id
- action                        APPROVED, REJECTED, REMOVED
- reason
- created_at                    UTC
~~~

### Required indexes

Create indexes on:

~~~text
listings.city
listings.state
listings.zip_code
listings.status
listings.host_id
bookings.listing_id
bookings.check_in
bookings.check_out
bookings.status
reviews.listing_id
~~~

### Required constraints

- User email is unique.
- Listing host references a Host user.
- Check-out is after check-in.
- Rating is between 1 and 5.
- A booking has at most one review.
- Booking creation uses a database transaction.
- Foreign keys protect related data.
- Removed listings are retained for historical analytics.
- Confirmed bookings cannot overlap for the same listing.

---

## 7. API Design

All requests and responses use JSON.

All public routes use the version prefix:

~~~text
/api/v1/
~~~

### Standard success response

~~~json
{
  "success": true,
  "data": {},
  "message": "Request completed successfully"
}
~~~

### Standard error response

~~~json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request",
    "details": [
      {
        "field": "check_out",
        "message": "Check-out must be after check-in"
      }
    ]
  }
}
~~~

### HTTP status codes

| Status | Meaning |
|---|---|
| 200 | Successful read or update |
| 201 | Resource created |
| 400 | Invalid input |
| 401 | Not authenticated |
| 403 | Insufficient permission |
| 404 | Resource not found |
| 409 | Booking or duplicate conflict |
| 500 | Unexpected server error |

### Pagination

Search and review endpoints support:

~~~text
page
page_size
~~~

Example:

~~~text
GET /api/v1/listings/search?page=1&page_size=10
~~~

Paginated responses include:

~~~json
{
  "success": true,
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_items": 25,
    "total_pages": 3
  }
}
~~~

### Authentication endpoints

~~~text
POST /api/v1/auth/register/customer
POST /api/v1/auth/register/host
POST /api/v1/auth/login
GET  /api/v1/auth/me
~~~

Admin accounts are created through seed data.

### Customer endpoints

~~~text
GET  /api/v1/listings/search
GET  /api/v1/listings/{listing_id}
GET  /api/v1/listings/{listing_id}/availability
GET  /api/v1/listings/{listing_id}/reviews

POST /api/v1/bookings
GET  /api/v1/bookings/my
GET  /api/v1/bookings/{booking_id}
PATCH /api/v1/bookings/{booking_id}/cancel

POST /api/v1/reviews
~~~

Search parameters:

~~~text
check_in
check_out
start_time
end_time
guests
city
state
zip_code
latitude
longitude
radius
min_price
max_price
amenities
page
page_size
~~~

Listing search responses include:

~~~json
{
  "id": 1,
  "name": "Sunny San Jose Home",
  "cost_per_night": 220,
  "cost_rating": "$$$",
  "average_rating": 4.7,
  "review_count": 18,
  "bookings_today": 4,
  "latitude": 37.3382,
  "longitude": -121.8863,
  "available": true
}
~~~

### Host endpoints

~~~text
POST   /api/v1/host/listings
GET    /api/v1/host/listings
GET    /api/v1/host/listings/{listing_id}
PATCH  /api/v1/host/listings/{listing_id}
DELETE /api/v1/host/listings/{listing_id}

POST   /api/v1/host/listings/{listing_id}/media
DELETE /api/v1/host/listings/{listing_id}/media/{media_id}

GET /api/v1/host/analytics
~~~

### Admin endpoints

~~~text
GET    /api/v1/admin/listings/pending
PATCH  /api/v1/admin/listings/{listing_id}/approve
PATCH  /api/v1/admin/listings/{listing_id}/reject
DELETE /api/v1/admin/listings/{listing_id}
GET    /api/v1/admin/analytics
GET    /api/v1/admin/audit-actions
~~~

### Health and documentation

~~~text
GET /health
GET /docs
GET /redoc
~~~

FastAPI automatically generates Swagger/OpenAPI documentation.

### Endpoint documentation requirement

Every endpoint must document:

- Request example
- Success response example
- Validation errors
- Required role
- Possible HTTP status codes
- Authentication requirement

---

## 8. Business Rules

### Stay duration

- Minimum stay is 1 night.
- Maximum stay is 14 nights.
- Check-out must be after check-in.
- Dates use ISO format: YYYY-MM-DD.
- Requested times must be inside the listing's booking window.

### Guest limit

~~~text
requested_guests <= listing.max_guests
~~~

### Listing visibility

Customers can search only listings with status APPROVED.

PENDING, REJECTED, and REMOVED listings are hidden from customer search.

### Cost calculation

~~~text
number_of_nights = check_out - check_in
total_cost = number_of_nights * cost_per_night
~~~

### Bookings today

The listing response includes the number of bookings created today:

~~~text
bookings_today =
count of confirmed bookings where created_at falls on today's application date
~~~

All stored timestamps use UTC. Display dates use the configured application timezone.

### Booking overlap

An existing booking overlaps the requested dates when:

~~~text
existing_check_in < requested_check_out
AND existing_check_out > requested_check_in
~~~

If times are supplied, the same rule applies to the requested datetime range.

### Double-booking protection

Booking creation must:

1. Start a database transaction.
2. Lock the listing row using a row-level lock.
3. Check overlapping confirmed bookings.
4. Check blocked availability ranges.
5. Validate guest count and time window.
6. Calculate total cost.
7. Create the booking.
8. Commit the transaction.

If feasible, add a PostgreSQL date-range exclusion constraint for confirmed bookings. Otherwise, the row lock and transaction are mandatory.

Overlapping bookings return HTTP 409.

### Soft deletion

Listings and bookings are not permanently deleted.

- Host removal sets listing status to REMOVED.
- Admin removal sets listing status to REMOVED.
- Removed listings are excluded from customer search.
- Historical bookings, reviews, and analytics remain available.
- Admin action is recorded in admin_actions.

### Review rules

- Customer must own the booking.
- Booking must be COMPLETED.
- One review per booking.
- Rating must be between 1 and 5.

---

## 9. Authentication and Security

### JWT flow

~~~text
User logs in
    ↓
FastAPI validates credentials
    ↓
JWT token returned
    ↓
Frontend sends Authorization: Bearer token
    ↓
FastAPI verifies token and role
~~~

### Security requirements

- Hash passwords with bcrypt.
- Never return password hashes.
- Use JWT expiration.
- Validate every request body, query parameter, and path parameter.
- Use role dependencies such as require_customer, require_host, and require_admin.
- Store secrets in environment variables.
- Enable CORS only for the frontend origin.
- Add request logging and request IDs.
- Never commit environment files or API keys.
- Use generic login failure messages.
- Protect admin audit endpoints.

---

## 10. Google Maps

Google Maps will be added after core backend functionality works.

The database stores:

~~~text
address
city
state
zip_code
latitude
longitude
~~~

The backend returns coordinates with listing results. The React frontend displays markers and map locations.

### Cost-control approach

- Seed coordinates manually for mock listings.
- Avoid repeatedly geocoding the same address.
- Restrict the API key by domain and API type.
- Enable only required Maps APIs.
- Set usage quotas and alerts.
- Keep the key in environment variables.
- Use Google Maps Embed for simple map display if appropriate.

The backend can start without Google Maps access because it stores coordinates independently.

---

## 11. Cost-Controlled Azure Deployment

### Local development: free

~~~text
FastAPI             Local
PostgreSQL          Docker container
React               Local
Swagger             Local
Pytest              Local
Images              Public mock URLs
~~~

No Azure resources are required during initial development.

### Final deployment

~~~text
Browser
   ↓ HTTPS
Azure Standard Load Balancer + public IP
   ├── VM 1: reverse proxy + React build + FastAPI container
   └── VM 2: same application, created by autoscaling
                    ↓ private database connection / TLS
          Azure PostgreSQL Flexible Server
~~~

### What we deploy

| Component | Purpose |
|---|---|
| Resource group | Groups the project's Azure resources for tracking and eventual cleanup |
| Virtual network, application subnet, database subnet, and security rules | Connects the application to PostgreSQL and limits exposed ports |
| Standard public Load Balancer, public IP, health probe, and outbound rule | Public entry point, traffic distribution, readiness checks, and VM internet access |
| VM Scale Set and autoscale configuration | Runs one VM normally and can add a second under load; maximum two |
| Application software on each VM | FastAPI backend, compiled React frontend, and an HTTPS reverse proxy; no separate frontend hosting service needed |
| PostgreSQL Flexible Server and required private DNS | Stores users, listings, bookings, reviews, and analytics data privately |
| VM operating-system disks | Required VM storage; include their cost in the estimate |
| Basic metrics, budget alerts, and cleanup runbook | Provides operational evidence and controls runtime and credit usage |

The reverse proxy handles HTTPS on each VM. React is served from the same hostname as the API. Application modules (authentication, listings, bookings, reviews, analytics, and moderation) run together in one FastAPI application, not on separate servers. Google Maps remains an external Google service, and GitHub remains the code/journal repository.

Verify regional resource prices, free allowances, DNS/certificate setup, and the required evaluation duration before provisioning. Private PostgreSQL networking may require a private DNS zone; include it in the estimate. Budget alerts are notifications, not automatic spending caps.

References: [Azure VM Scale Sets](https://learn.microsoft.com/en-us/azure/virtual-machine-scale-sets/overview), [PostgreSQL private networking](https://learn.microsoft.com/en-us/azure/postgresql/network/concepts-networking-private), [Load Balancer outbound rules](https://learn.microsoft.com/en-us/azure/load-balancer/outbound-rules).

### Minimum-resource strategy

| Resource | Development | Final demo |
|---|---|---|
| VM Scale Set | Minimum 1 instance | Temporarily scale to 2 |
| VM size | Smallest eligible burstable VM | Same |
| PostgreSQL | Smallest eligible server | Same |
| Load balancer | Create near the end | Keep briefly |
| Storage | Database URLs only | No cloud file storage |
| Monitoring | Local logs | Minimal Azure Monitor |

### Deployment acceptance

The deployed architecture must show:

- A VM Scale Set resource.
- An autoscaling policy.
- A Load Balancer with a health probe.
- At least one healthy FastAPI instance.
- A PostgreSQL database connected to the API.
- A public API URL.
- Working health and Swagger endpoints.

For the demonstration, use two healthy instances and record a controlled autoscaling event. Keep the deployment available for the instructor's evaluation window, then export evidence/data and delete project resources.

### Azure safety rules

- Check remaining credit before deployment.
- Create budget and email alerts.
- Never upgrade to Pay-As-You-Go.
- Do not create NAT Gateway.
- Do not create Kubernetes resources.
- Do not create unnecessary public IP addresses.
- Test locally before cloud provisioning.
- Delete resources after the instructor's evaluation window, using the documented project-only cleanup procedure.
- Verify that the resource group is empty after deletion.

### Cloud fallback

If Azure quotas, cost, or account limitations prevent the required deployment:

1. Do not upgrade the account.
2. Save screenshots of the limitation.
3. Ask the instructor for written approval to use an equivalent provider.
4. Use a cloud provider with VM autoscaling, a load balancer, and managed PostgreSQL.
5. Document the approved alternative in the journal and README.

The exact Azure cost cannot be guaranteed to be zero because load balancing and networking may consume credit.

---

## 12. Testing and Mock Data

### Testing tools

Use Pytest and HTTPX.

### Required tests

Authentication:

- Customer registration
- Host registration
- Duplicate email rejection
- Invalid login rejection
- Valid JWT
- Invalid or expired JWT

Authorization:

- Customer cannot access Admin APIs.
- Customer cannot access Host APIs.
- Host cannot edit another Host's listing.
- Unauthenticated user cannot create a booking.
- Admin can approve a listing.

Listings and search:

- Create, update, and remove listing.
- Admin approval and rejection.
- Search by city, state, ZIP, dates, times, guests, and availability.
- Unapproved listings are hidden.
- Removed listings are hidden.
- Stays longer than 14 days are rejected.
- Cost rating is returned.
- Bookings today is returned.

Bookings:

- Valid booking succeeds.
- Overlapping booking is rejected.
- Simultaneous booking attempts cannot both succeed.
- Guest limit is enforced.
- Booking time window is enforced.
- Total cost is correct.
- Customer can cancel own booking.
- Customer cannot cancel another customer's booking.
- Removed listing cannot receive a new booking.

Reviews:

- Completed booking review succeeds.
- Future booking review fails.
- Duplicate review fails.
- Invalid rating fails.

Analytics:

- Host sees only personal analytics.
- Admin sees system-wide analytics.
- 30, 60, and 90-day filters work.
- ZIP-code grouping works.
- Removed listings remain available in historical analytics where appropriate.

### Mock data

Seed:

- 1 Admin
- 2 Hosts
- 3 Customers
- 10–15 listings
- At least 4 ZIP codes
- Approved, pending, rejected, and removed listings
- Different prices and guest limits
- Different cost ratings
- Multiple amenities and media URLs
- Different hours and booking windows
- Past, current, and future bookings
- Cancelled and completed bookings
- Reviews and ratings
- Bookings across 30, 60, and 90 days
- Coordinates for every listing

Use fake credentials only.

---

## 13. Team Responsibilities

### Backend owner — [Your Name]

- FastAPI setup
- Database and SQLAlchemy models
- Alembic migrations
- Authentication and authorization
- Customer, Host, and Admin APIs
- Booking conflict logic
- Reviews and ratings
- Analytics
- Mock data
- Automated tests
- Azure deployment
- Swagger documentation
- Frontend API integration

### Frontend owner — [Teammate Name]

- React application
- Customer screens
- Host screens
- Admin screens
- Navigation and styling
- Wireframes
- Map display
- Frontend API calls
- Frontend deployment

### Shared work

Both members contribute to:

- Requirements analysis
- API contract decisions
- Testing
- Frontend/backend integration
- Architecture and database diagrams
- README
- Project journal
- Scrum meetings
- Sprint planning
- Code reviews
- Demo preparation

All work must be visible through GitHub commits, issues, and pull requests.

---

## 14. Agile Artifacts

### Repository structure

~~~text
README.md
backend/
frontend/
docs/
├── component-diagram.md
├── component-diagram.png
├── deployment-diagram.md
├── deployment-diagram.png
├── database-schema.md
├── design-decisions.md
└── api-testing.md
journal/
├── week-1.md
├── week-2.md
├── week-3.md
└── week-4.md
wireframes/
openapi.yaml
.env.example
~~~

### Weekly Scrum report

Every report answers:

~~~text
What tasks did I work on or complete?
What am I planning to work on next?
What tasks are blocked waiting on another team member?
~~~

Also include commit links, issue links, testing completed, problems, and decisions.

### XP values

Select:

Communication:
- API contract discussions
- Integration meetings
- Shared task board
- Pull-request reviews
- Blocker documentation

Feedback:
- Frontend API testing
- Changes based on integration feedback
- Demo feedback
- Test failures and fixes
- Improved validation and error messages

Maintain:

- Product backlog
- Sprint backlog for every sprint
- Task board
- Burndown chart
- Story status updates

Include all links in the README.

---

## 15. Sprint Schedule

### Sprint 1 — Foundation

- Repository setup
- FastAPI structure
- Local PostgreSQL
- SQLAlchemy
- Alembic
- Database diagram
- Error handling
- Swagger
- Health endpoint
- API versioning
- Product and sprint backlogs

### Sprint 2 — Authentication and Listings

- Customer registration
- Host registration
- Login
- JWT
- Role authorization
- Host listing CRUD
- Hours and booking windows
- Admin approval
- Search
- Pagination
- Listing details

### Sprint 3 — Bookings and Reviews

- Availability
- Booking creation
- 14-day validation
- Time-window validation
- Database locking
- Overlap prevention
- Cancellation
- Booking history
- Reviews
- Ratings
- Cost rating
- Bookings today
- Automated tests

### Sprint 4 — Analytics and Deployment

- Host analytics
- Admin analytics
- 30, 60, and 90-day filters
- ZIP-code analytics
- Admin audit log
- Frontend integration
- Google Maps
- Azure deployment
- Documentation
- Demo rehearsal

### Calendar plan

| Dates | Work |
|---|---|
| Nov 14–15 | Approve design, verify Azure, repository, backlog |
| Nov 16–17 | FastAPI, database, migrations, Swagger, API versioning |
| Nov 18–19 | Authentication and roles |
| Nov 20–22 | Listings, hours, booking windows, search |
| Nov 23–25 | Bookings, locking, cancellation, reviews |
| Nov 26–27 | Analytics, audit log, frontend integration, maps |
| Nov 28–29 | Docker and Azure deployment |
| Nov 30–Dec 1 | Documentation, testing, rehearsal |
| Dec 2 | Final verification and submission |

---

## 16. Integration Plan

Do not wait until the entire backend is complete.

### Integration milestone 1

Connect:

~~~text
Login → Search → Listing Details
~~~

Verify:

- Login token is stored.
- Authorization header is sent.
- Search filters work.
- Listing coordinates display.
- API errors appear in the UI.

### Integration milestone 2

Connect:

~~~text
Create Booking → View Booking → Cancel Booking
~~~

Verify:

- Booking dates are sent correctly.
- 14-night validation appears.
- Booking conflict errors appear.
- Customer sees only personal bookings.

### Integration milestone 3

Connect:

~~~text
Host Listing Management → Admin Approval → Analytics
~~~

Verify:

- Host sees only personal listings.
- Admin approval changes listing visibility.
- Host and Admin analytics have different scopes.
- 30, 60, and 90-day filters work.

### Frontend/backend contract

Before implementation, agree on:

- Endpoint names
- Request fields
- Response fields
- Error format
- JWT header format
- Role names
- Date and time formats
- Listing statuses
- Booking statuses
- Pagination format

Swagger/OpenAPI is the shared contract.

---

## 17. Demo Plan

1. Customer logs in.
2. Customer searches by dates, time, guests, and ZIP code.
3. Customer views listing details.
4. Customer sees photos, amenities, cost rating, ratings, and map location.
5. Customer books an available listing.
6. A second overlapping booking is rejected.
7. Customer views booking history.
8. Customer cancels a booking or reviews a completed booking.
9. Host creates or updates a listing.
10. Admin approves the listing.
11. Host views 30, 60, and 90-day analytics.
12. Admin views system-wide ZIP-code analytics.
13. Team shows Swagger, deployed API, diagrams, GitHub history, and project artifacts.

### Deployment evidence

Show:

- Azure subscription
- VM Scale Set
- Number of instances
- Autoscaling configuration
- Load Balancer
- Health probe
- PostgreSQL database
- Public API URL
- Health endpoint
- Swagger page
- React frontend calling the API
- Cost-management alert configuration

---

## 18. Definition of Done

A feature is complete only when:

- The endpoint is implemented.
- Input validation exists.
- Authentication and authorization are correct.
- JSON success and error responses work.
- Automated tests pass.
- Swagger documents the endpoint.
- Request and response examples are documented.
- The frontend can call the endpoint.
- The feature works in the integrated vertical flow.
- Code is committed to GitHub.
- A pull request or issue documents the work.
- Related README, journal, or design documentation is updated.

---

## 19. Final Checklist

### Functionality

- [ ] Customer registration
- [ ] Host registration
- [ ] Customer login
- [ ] Host login
- [ ] Admin login
- [ ] Role-based authorization
- [ ] Search by date
- [ ] Search by time
- [ ] Search by guests
- [ ] Search by duration
- [ ] Search by availability
- [ ] Search by city/state
- [ ] Search by ZIP code
- [ ] Maximum 14-night validation
- [ ] Google Maps or approved map integration
- [ ] Listing photos/videos
- [ ] Amenities
- [ ] Cost per night
- [ ] Cost rating
- [ ] Reviews and ratings
- [ ] Number of bookings today
- [ ] Booking creation
- [ ] Double-booking prevention
- [ ] Booking cancellation
- [ ] Past-booking reviews
- [ ] Host listing creation
- [ ] Host listing update
- [ ] Host listing view
- [ ] Host listing soft removal
- [ ] Host ownership protection
- [ ] Admin approval
- [ ] Admin rejection
- [ ] Admin soft removal
- [ ] Admin audit log
- [ ] Host analytics
- [ ] Admin analytics
- [ ] 30-day analytics
- [ ] 60-day analytics
- [ ] 90-day analytics
- [ ] ZIP-code analytics

### API quality

- [ ] Versioned API routes
- [ ] JSON request and response bodies
- [ ] Pydantic validation
- [ ] Consistent error responses
- [ ] Correct HTTP status codes
- [ ] Pagination
- [ ] Database indexes
- [ ] Swagger/OpenAPI documentation
- [ ] Request examples
- [ ] Response examples
- [ ] Authentication tests
- [ ] Authorization tests
- [ ] Booking conflict tests
- [ ] Analytics tests

### Cloud

- [ ] Azure VM Scale Set
- [ ] Azure Load Balancer
- [ ] Azure PostgreSQL
- [ ] Autoscaling policy
- [ ] Load-balancer health probe
- [ ] Public API URL
- [ ] Health endpoint
- [ ] Deployed Swagger
- [ ] Frontend calls deployed API
- [ ] Budget alerts
- [ ] Cloud fallback approval if needed
- [ ] Resources deleted after demo

### Project process

- [ ] README
- [ ] Team name and members
- [ ] Contribution summary
- [ ] Project journal link
- [ ] Product backlog link
- [ ] Sprint backlog links
- [ ] Burndown chart
- [ ] Weekly Scrum reports
- [ ] Communication documented
- [ ] Feedback documented
- [ ] Component diagram
- [ ] Deployment diagram
- [ ] Database diagram
- [ ] UI wireframes
- [ ] Visible commits for every member
- [ ] Demo rehearsed

---

## Approval Decisions

Before implementation begins, approve:

- [ ] FastAPI, SQLAlchemy, PostgreSQL, and React
- [ ] Azure VM Scale Set, Load Balancer, and PostgreSQL
- [ ] Local development before cloud deployment
- [ ] Minimum VM Scale Set size of 1 and maximum of 2
- [ ] Mock media URLs instead of cloud file storage
- [ ] Seeded coordinates before Google address search
- [ ] Soft deletion for listings
- [ ] Database locking and overlap protection
- [ ] API versioning and pagination
- [ ] Cost rating and bookings-today calculation
- [ ] Admin audit log
- [ ] Backend and frontend ownership
- [ ] Early vertical-slice integration
- [ ] Sprint schedule
- [ ] XP values: Communication and Feedback
- [ ] Instructor acceptance of Azure as the EC2-equivalent deployment

### Final cost note

This plan minimizes Azure usage, but exact $0 cost cannot be guaranteed because load balancing and networking may consume Azure credit. The team will develop locally first, use the smallest resources, monitor usage, avoid Pay-As-You-Go, and delete cloud resources after the demo.
