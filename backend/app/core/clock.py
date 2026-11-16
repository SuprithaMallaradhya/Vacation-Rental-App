from datetime import UTC, datetime


def utc_now() -> datetime:
    """Request clock, overridable in boundary/DST tests."""
    return datetime.now(UTC)
