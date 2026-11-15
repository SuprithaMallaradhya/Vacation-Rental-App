import os

from app.core.config import get_settings


def test_development_and_test_database_urls_are_distinct() -> None:
    settings = get_settings()
    test_url = os.environ["TEST_DATABASE_URL"]
    assert settings.database_url != test_url
    assert "vacation_rental_dev" not in test_url
    assert ":5432/" not in test_url
