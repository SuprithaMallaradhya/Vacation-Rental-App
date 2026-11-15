import os

test_database_url = os.getenv("TEST_DATABASE_URL")
if not test_database_url:
    raise RuntimeError("TEST_DATABASE_URL must be explicitly set for backend tests")
if "vacation_rental_dev" in test_database_url or ":5432/" in test_database_url:
    raise RuntimeError("TEST_DATABASE_URL points at the development database")
