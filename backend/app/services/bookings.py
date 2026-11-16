from collections.abc import Callable
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError
from app.models import Booking, ListingBookingRule
from app.models.enums import ListingStatus, ReservationState
from app.schemas.bookings import BookingCreate, BookingResponse
from app.schemas.common import Paginated
from app.services import listings
from app.services.availability import StayError, occupied_listing_ids, resolve_listing_stay

Clock = Callable[[], datetime]


def confirmation(booking: Booking, now: datetime) -> BookingResponse:
    """Use accepted snapshots, including after listing edits/removal."""
    cancelled = booking.reservation_state == ReservationState.CANCELLED
    timezone = ZoneInfo(booking.listing_timezone_snapshot)
    return BookingResponse.model_validate(
        {
            **{field: getattr(booking, field) for field in Booking.__table__.columns.keys()},
            "nights": (booking.check_out - booking.check_in).days,
            "check_in_time": booking.arrival_at.astimezone(timezone).time(),
            "check_out_time": booking.departure_at.astimezone(timezone).time(),
            "status": "CANCELLED"
            if cancelled
            else "COMPLETED"
            if booking.departure_at <= now
            else "CONFIRMED",
            "can_cancel": not cancelled and now < booking.arrival_at,
        }
    )


async def owned_booking(session: AsyncSession, customer_id: UUID, booking_id: UUID, *, lock=False):
    statement = select(Booking).where(Booking.id == booking_id, Booking.customer_id == customer_id)
    if lock:
        statement = statement.with_for_update()
    booking = await session.scalar(statement.execution_options(populate_existing=True))
    if booking is None:
        raise APIError(404, "NOT_FOUND", "Booking not found")
    return booking


async def create_booking(
    session: AsyncSession, customer_id: UUID, request: BookingCreate, clock: Clock
) -> BookingResponse:
    # Auth already began this request's transaction. Keep the listing lock through
    # all validation, snapshot insertion and commit, just like other writers.
    try:
        listing = await listings.lock_listing(session, request.listing_id)
        if listing.status != ListingStatus.APPROVED:
            raise APIError(409, "LISTING_UNAVAILABLE", "Listing is not available for booking")
        rules = list(
            (
                await session.scalars(
                    select(ListingBookingRule).where(ListingBookingRule.listing_id == listing.id)
                )
            ).all()
        )
        stay_request = request.stay_request()
        occupied = await occupied_listing_ids(session, [listing.id], stay_request)
        now = clock()
        try:
            stay = resolve_listing_stay(listing, stay_request, rules, now)
        except StayError as exc:
            raise APIError(
                422, exc.code, str(exc), details=[{"field": exc.field, "message": str(exc)}]
            ) from None
        if listing.id in occupied:
            raise APIError(409, "DATES_UNAVAILABLE", "Requested nights are not available")
        address = ", ".join(
            part
            for part in (
                listing.address_line1,
                listing.address_line2,
                listing.city,
                listing.state,
                listing.zip_code,
            )
            if part
        )
        booking = Booking(
            listing_id=listing.id,
            customer_id=customer_id,
            check_in=stay.check_in,
            check_out=stay.check_out,
            arrival_at=stay.arrival_at,
            departure_at=stay.departure_at,
            guests=stay.guests,
            nightly_price_snapshot=stay.nightly_price,
            total_cost=stay.total_cost,
            currency=stay.currency,
            listing_name_snapshot=listing.name,
            listing_address_snapshot=address,
            listing_zip_snapshot=listing.zip_code,
            listing_timezone_snapshot=listing.timezone,
            reservation_state=ReservationState.CONFIRMED,
            cancelled_at=None,
            created_at=now,
            updated_at=now,
        )
        session.add(booking)
        await session.flush()
        result = confirmation(booking, now)
        await session.commit()
        return result
    except IntegrityError as exc:
        await session.rollback()
        # PostgreSQL exclusion is a second defense against writers that bypass
        # the service. Inspect structured driver metadata, never SQL/error text.
        cause = getattr(exc.orig, "__cause__", None)
        if getattr(cause, "constraint_name", None) == "ex_bookings_no_confirmed_overlap":
            raise APIError(409, "DATES_UNAVAILABLE", "Requested nights are not available") from None
        raise
    except Exception:
        await session.rollback()
        raise


async def booking_detail(session, customer_id, booking_id, clock: Clock) -> BookingResponse:
    booking = await owned_booking(session, customer_id, booking_id)
    return confirmation(booking, clock())


async def booking_history(session, customer_id, page, page_size, clock: Clock):
    condition = Booking.customer_id == customer_id
    total = await session.scalar(select(func.count()).select_from(Booking).where(condition))
    offset = (page - 1) * page_size
    rows = []
    # An arbitrarily large out-of-range page is still an empty page; do not
    # overflow PostgreSQL's bigint OFFSET parameter for valid positive integers.
    if offset < total:
        rows = (
            await session.scalars(
                select(Booking)
                .where(condition)
                .order_by(Booking.created_at.desc(), Booking.id)
                .offset(offset)
                .limit(page_size)
            )
        ).all()
    now = clock()
    return Paginated(
        data=[confirmation(row, now) for row in rows],
        pagination=listings.pagination(page, page_size, total),
    )


async def cancel_booking(session, customer_id, booking_id, clock: Clock) -> BookingResponse:
    try:
        # Read only the owned parent ID first; do not lock a booking before its
        # listing, and never lock a foreign customer's listing on their behalf.
        listing_id = await session.scalar(
            select(Booking.listing_id).where(
                Booking.id == booking_id, Booking.customer_id == customer_id
            )
        )
        if listing_id is None:
            raise APIError(404, "NOT_FOUND", "Booking not found")
        await listings.lock_listing(session, listing_id)
        booking = await owned_booking(session, customer_id, booking_id, lock=True)
        now = clock()
        if booking.reservation_state != ReservationState.CANCELLED:
            if now >= booking.arrival_at:
                raise APIError(409, "CANCELLATION_CLOSED", "Cancellation closes at arrival")
            # Explicit UPDATE includes updated_at even if a frozen clock equals
            # the original timestamp; ORM onupdate must not substitute DB time.
            booking = (
                await session.scalars(
                    update(Booking)
                    .where(Booking.id == booking.id)
                    .values(
                        reservation_state=ReservationState.CANCELLED,
                        cancelled_at=now,
                        updated_at=now,
                    )
                    .returning(Booking)
                    .execution_options(populate_existing=True)
                )
            ).one()
        result = confirmation(booking, now)
        await session.commit()
        return result
    except Exception:
        await session.rollback()
        raise
