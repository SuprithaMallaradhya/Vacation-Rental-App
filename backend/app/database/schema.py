from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

SCHEMA_REVISION = "0001_initial_schema"
REQUIRED_TABLES = (
    "users",
    "listings",
    "listing_hours",
    "listing_booking_rules",
    "listing_media",
    "amenities",
    "listing_amenities",
    "availability_blocks",
    "bookings",
    "reviews",
    "admin_actions",
)


async def schema_is_current(session: AsyncSession) -> bool:
    if not await session.scalar(text("SELECT to_regclass('alembic_version')")):
        return False
    revisions = set((await session.scalars(text("SELECT version_num FROM alembic_version"))).all())
    if revisions != {SCHEMA_REVISION}:
        return False
    for table in REQUIRED_TABLES:
        if not await session.scalar(text("SELECT to_regclass(:name)"), {"name": table}):
            return False
    return True
