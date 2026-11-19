PYTHON ?= python3.12
VENV := backend/.venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

setup:
	@command -v $(PYTHON) >/dev/null || (echo "Python 3.12 is required; install it and rerun make setup." && exit 1)
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e 'backend[dev]'

db-up:
	docker compose up -d --wait postgres-dev postgres-test

db-down:
	docker compose stop postgres-dev postgres-test

migrate:
	cd backend && ../$(PY) -m alembic upgrade head

seed:
	cd backend && ../$(PY) -m seed.demo

api:
	cd backend && ../$(PY) -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --no-proxy-headers

test:
	cd backend && TEST_DATABASE_URL=$${TEST_DATABASE_URL:-postgresql+asyncpg://vacation:vacation@127.0.0.1:55433/vacation_rental_test} ../$(PY) -m pytest $${TEST_PATH:-tests}

lint:
	$(PY) -m ruff check backend

openapi:
	cd backend && ../$(PY) -c 'import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))' > ../docs/openapi.json

schema-check:
	cd backend && ../$(PY) -m alembic check

verify: lint test schema-check

PROD_COMPOSE := docker compose -f deploy/compose.prod.yaml -f deploy/compose.build.yaml

# Production images (nginx + React build + FastAPI) on http://localhost:8080,
# using the local dev database. Needs deploy/.env.prod (copy deploy/.env.prod.example).
prod-local-up:
	@test -f deploy/.env.prod || (echo "Create deploy/.env.prod first: cp deploy/.env.prod.example deploy/.env.prod (set JWT_SECRET_KEY)" && exit 1)
	$(PROD_COMPOSE) up -d --build --wait
	@echo "Open http://localhost:8080  (health: http://localhost:8080/ready)"

prod-local-down:
	$(PROD_COMPOSE) down
