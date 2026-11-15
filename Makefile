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
	docker compose up -d postgres-dev postgres-test

db-down:
	docker compose stop postgres-dev postgres-test

migrate:
	@echo "Phase 2: migrations are not implemented yet."
	@exit 1

seed:
	@echo "Phase 2: seed data is not implemented yet."
	@exit 1

api:
	cd backend && ../$(PY) -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

test:
	cd backend && TEST_DATABASE_URL=$${TEST_DATABASE_URL:-postgresql+asyncpg://vacation:vacation@localhost:5433/vacation_rental_test} ../$(PY) -m pytest $${TEST_PATH:-tests}

lint:
	$(PY) -m ruff check backend

openapi:
	cd backend && ../$(PY) -c 'import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))' > ../docs/openapi.json

verify: lint test

prod-local-up:
	@echo "Phase 10: production-like proxy/UI packaging is not implemented yet."
	@exit 1
