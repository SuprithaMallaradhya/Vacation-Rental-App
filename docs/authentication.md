# Authentication and frontend handoff

Phase 3 implements the four auth endpoints under `/api/v1/auth`. There is no public Admin registration. Host/Customer roles are selected by the signup endpoint and cannot be supplied in JSON. Admin credentials come from the explicit local demo seed.

## Start and try it

```bash
make setup
make db-up
make migrate
make seed
make api
```

Open `http://127.0.0.1:8000/docs`. Expand `POST /api/v1/auth/login`, choose Try it out, and submit the JSON example. Copy `data.access_token` into Swagger's **Authorize** dialog, then execute `GET /api/v1/auth/me`. Paste just the token; Swagger adds the `Bearer` prefix. This is HTTP bearer authentication, not an OAuth form login.

The seeded logins are `customer1@example.test` through `customer3@example.test`, `host1@example.test`, `host2@example.test`, and `admin@example.test`. All use the intentionally public local demo password `DemoOnly!2026`. These accounts are fictional and must not be used as real deployment credentials.

Example login (its response contains an access token; do not paste it into logs or commit it):

```bash
curl -sS http://127.0.0.1:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"customer1@example.test","password":"DemoOnly!2026"}'
```

## Requests and responses

| Endpoint | Access / input | Success |
|---|---|---|
| `POST /api/v1/auth/register/customer` | Public; name, email, phone, password | 201; `success/data` with safe user fields; role CUSTOMER |
| `POST /api/v1/auth/register/host` | Same fields | 201; safe user; role HOST |
| `POST /api/v1/auth/login` | Public; email and password as JSON | 200; access_token, token_type, expires_in, expires_at, user inside `data` |
| `GET /api/v1/auth/me` | `Authorization: Bearer <access_token>` | 200; current safe user inside `data` |

Safe user fields: `id`, `name`, `email`, `phone`, `role`, and UTC `created_at`. Passwords and password hashes are never part of a user response. Registration does not automatically log the user in; call login afterward.

All request bodies reject unexpected properties, including `role`, `id`, and `password_hash`. Email is trimmed, normalized to lowercase with ASCII domain normalization, and syntax-validated without DNS calls. The reserved `.test` suffix supports the local demo. Internationalized local parts are currently unsupported. Signup requires a nonblank name up to 120 characters and a phone of 8–32 characters using digits and optional `+`, spaces, parentheses, or hyphens.

Passwords preserve whitespace and use bcrypt. Signup accepts 8–72 **UTF-8 bytes**; login accepts 1–72 bytes for compatibility with stored accounts. A non-ASCII character may use multiple bytes. Inputs over 72 bytes are rejected rather than silently truncated.

See [mock request/response fixtures](fixtures/auth.json). These are illustrative frontend fixtures; the token placeholder is not an actual credential. Swagger also documents request examples, response schemas, errors, and bearer authentication.

## Error handling for React

All errors use `success=false`, `error.code/message/details`, and a matching `request_id`/`X-Request-ID` header. Body parse errors return 400 `INVALID_JSON`; field validation returns 422 `VALIDATION_ERROR`. Input values and passwords are not echoed in validation details.

| Status / code | React action |
|---|---|
| 401 `INVALID_CREDENTIALS` | Show the generic login failure; unknown email and wrong password have the same response |
| 401 `UNAUTHENTICATED` | Clear any stale in-memory token and return to login |
| 403 `FORBIDDEN` | Show insufficient permission; do not retry unchanged credentials |
| 409 `EMAIL_ALREADY_REGISTERED` | Show an email conflict and allow correction or login |
| 422 `VALIDATION_ERROR` | Match `details[].field` to form fields |
| 429 `RATE_LIMITED` | Respect the `Retry-After` header before another login attempt |

401 responses preserve `WWW-Authenticate: Bearer`. Login/current-user responses use `Cache-Control: no-store`, and login also uses `Pragma: no-cache`. CORS exposes request IDs and Retry-After to the two configured React development origins.

## Tokens and authorization

Access tokens expire after `JWT_EXPIRE_MINUTES` (default 60). `expires_in` is seconds (default 3600); `expires_at` is UTC. React should keep the token in memory and attach the Authorization header to protected API calls. Logout clears the in-memory token. No refresh-token or server-side logout/revocation endpoint is included; a copied token remains valid until expiry while its user exists.

Tokens contain a UUID `sub`, `iat`, `exp`, fixed issuer/audience, `type=access`, and unique `jti`. The decoder permits only HS256 and requires all these claims. It verifies signature, expiry, issue time, issuer, audience, token type, and subject format. The current user and role are loaded from PostgreSQL on each request; a role copied into a token is not an authority. Deleted users cannot authenticate.

`get_current_user`, `require_customer`, `require_host`, `require_admin`, and `require_owned` are reusable dependencies/helpers. Ownership failures return the same 404 for missing and foreign resources. Test-only role endpoints verify 403 behavior; they do not appear in the production API.

## Signing configuration and login throttle

When `JWT_SECRET_KEY` is blank in development/test, the process generates a random signing key. Tokens stop working after restart/reload. To preserve local tokens, generate a key with `python3.12 -c 'import secrets; print(secrets.token_urlsafe(48))'` and save it only in the ignored `backend/.env`. Outside development/test, a configured key of at least 32 UTF-8 bytes is mandatory. Never use the old example placeholder. The same secret must be supplied to all workers/VMs in a later deployment.

The prototype login limiter allows `LOGIN_MAX_ATTEMPTS=10` attempts per actual client IP during `LOGIN_WINDOW_SECONDS=60` seconds, including successful logins. It uses a sliding window and returns JSON 429 plus Retry-After. Its storage is bounded and process-local; counters reset on restart and are not shared across workers/VMs. This is basic local protection, not distributed brute-force prevention. No Redis or additional service is introduced.

The local Make/Docker startup disables proxy-header trust, preventing clients from changing their limiter identity via X-Forwarded-For. A later HTTPS reverse-proxy deployment must deliberately configure trusted proxies and a shared/edge limit. Behind an unconfigured proxy, all users may share one bucket. Registration has no dedicated rate limiter in this phase.

## Verification and integration status

Run `make test TEST_PATH=tests/auth`, then `make verify`. Tests use real migrations and isolated PostgreSQL schemas. They cover all roles, concurrent duplicate registration, password boundaries, forged/expired tokens, database-backed roles, deletion, validation, throttling, safe logs/responses, and Swagger contracts.

Backend tests and HTTP smoke checks do not prove the React screen works. Teammate contract review and React login plus one authenticated `/auth/me` call remain pending. Provide this setup and fixtures incrementally; no cloud deployment is needed to share the contract.

References: [FastAPI JWT security](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/), [PyJWT validation](https://pyjwt.readthedocs.io/en/stable/usage.html), [email-validator](https://pypi.org/project/email-validator/).
