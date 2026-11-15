from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import ValidationError
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError
from app.models import (
    AdminAction,
    Amenity,
    AvailabilityBlock,
    Booking,
    Listing,
    ListingAmenity,
    ListingBookingRule,
    ListingHours,
    ListingMedia,
    ListingRemoval,
)
from app.models.enums import AdminActionType, ListingStatus, MediaType, ReservationState
from app.schemas.common import Paginated, Pagination
from app.schemas.listings import (
    AuditResponse,
    BlockInput,
    BlockResponse,
    BookingRuleInput,
    HoursInput,
    ListingCreate,
    ListingDetail,
    ListingPatch,
    ListingSummary,
    MediaInput,
    MediaPatch,
    MediaResponse,
)

LOCATION_FIELDS = {
    "address_line1",
    "address_line2",
    "city",
    "state",
    "zip_code",
    "latitude",
    "longitude",
    "timezone",
}
MATERIAL_FIELDS = LOCATION_FIELDS | {"name", "description", "max_guests", "amenity_ids"}


def conflict(message: str, code="LISTING_CONFLICT") -> APIError:
    return APIError(409, code, message)


async def get_listing(
    session: AsyncSession, listing_id: UUID, *, host_id: UUID | None = None, lock: bool = False
) -> Listing:
    statement = select(Listing).where(Listing.id == listing_id)
    if host_id is not None:
        statement = statement.where(Listing.host_id == host_id)
    if lock:
        # All inventory/content writers must acquire this row FIRST. Refresh
        # cached state after waiting for another writer, including moderation.
        statement = statement.with_for_update().execution_options(populate_existing=True)
    listing = await session.scalar(statement)
    if listing is None:
        raise APIError(404, "NOT_FOUND", "Listing not found")
    return listing


async def lock_listing(session: AsyncSession, listing_id: UUID, *, host_id: UUID | None = None):
    return await get_listing(session, listing_id, host_id=host_id, lock=True)


def ensure_mutable(listing: Listing) -> None:
    if listing.status == ListingStatus.REMOVED:
        raise conflict("Removed listings cannot be changed", "LISTING_REMOVED")


def host_edit(listing: Listing, *, material=False, changed=True) -> None:
    if changed:
        if listing.status == ListingStatus.REJECTED or (
            listing.status == ListingStatus.APPROVED and material
        ):
            listing.status = ListingStatus.PENDING
        listing.updated_at = datetime.now(UTC)


def cost_rating(price: Decimal) -> str:
    return "$" if price < 100 else "$$" if price < 200 else "$$$" if price < 300 else "$$$$"


def listing_values(listing: Listing) -> dict:
    return {
        **{column.name: getattr(listing, column.name) for column in Listing.__table__.columns},
        "cost_rating": cost_rating(listing.nightly_price),
    }


async def listing_detail(session: AsyncSession, listing: Listing) -> ListingDetail:
    amenities = (
        await session.scalars(
            select(Amenity)
            .join(ListingAmenity)
            .where(ListingAmenity.listing_id == listing.id)
            .order_by(Amenity.name, Amenity.id)
        )
    ).all()
    media = (
        await session.scalars(
            select(ListingMedia)
            .where(ListingMedia.listing_id == listing.id)
            .order_by(ListingMedia.sort_order, ListingMedia.id)
        )
    ).all()
    hours = (
        await session.scalars(
            select(ListingHours)
            .where(ListingHours.listing_id == listing.id)
            .order_by(ListingHours.weekday)
        )
    ).all()
    rules = (
        await session.scalars(
            select(ListingBookingRule)
            .where(ListingBookingRule.listing_id == listing.id)
            .order_by(ListingBookingRule.weekday)
        )
    ).all()
    removal = await session.scalar(
        select(ListingRemoval).where(ListingRemoval.listing_id == listing.id)
    )
    return ListingDetail.model_validate(
        {
            **listing_values(listing),
            "amenities": amenities,
            "media": media,
            "hours": hours,
            "booking_rules": rules,
            "removal": removal,
        }
    )


async def finish(session: AsyncSession, listing: Listing) -> ListingDetail:
    await session.flush()
    await session.refresh(listing)
    result = await listing_detail(session, listing)
    await session.commit()
    return result


def pagination(page: int, page_size: int, total: int) -> Pagination:
    return Pagination(
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=(total + page_size - 1) // page_size,
    )


async def listing_page(
    session: AsyncSession,
    page: int,
    page_size: int,
    *,
    host_id: UUID | None = None,
    status: ListingStatus | None = None,
) -> Paginated[ListingSummary]:
    filters = []
    if host_id is not None:
        filters.append(Listing.host_id == host_id)
    if status is not None:
        filters.append(Listing.status == status)
    total = await session.scalar(select(func.count()).select_from(Listing).where(*filters))
    rows = (
        await session.scalars(
            select(Listing)
            .where(*filters)
            .order_by(Listing.created_at.desc(), Listing.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return Paginated(
        data=[ListingSummary.model_validate(listing_values(row)) for row in rows],
        pagination=pagination(page, page_size, total),
    )


async def validate_amenities(session: AsyncSession, ids: list[UUID]) -> None:
    found = set((await session.scalars(select(Amenity.id).where(Amenity.id.in_(ids)))).all())
    if found != set(ids):
        raise APIError(
            422,
            "VALIDATION_ERROR",
            "Unknown amenity IDs",
            details=[{"field": "amenity_ids", "message": "Use IDs from reference amenities"}],
        )


async def set_amenities(session: AsyncSession, listing_id: UUID, ids: list[UUID]) -> bool:
    await validate_amenities(session, ids)
    current = set(
        (
            await session.scalars(
                select(ListingAmenity.amenity_id).where(ListingAmenity.listing_id == listing_id)
            )
        ).all()
    )
    if current == set(ids):
        return False
    await session.execute(delete(ListingAmenity).where(ListingAmenity.listing_id == listing_id))
    session.add_all(
        ListingAmenity(listing_id=listing_id, amenity_id=identifier) for identifier in ids
    )
    return True


async def set_week(session: AsyncSession, listing_id: UUID, model: type, inputs: list) -> bool:
    current = {
        row.weekday: row
        for row in (
            await session.scalars(select(model).where(model.listing_id == listing_id))
        ).all()
    }
    changed = False
    for value in inputs:
        values = value.model_dump()
        row = current.get(value.weekday)
        if row is None:
            session.add(model(listing_id=listing_id, **values))
            changed = True
        else:
            for field, new_value in values.items():
                if getattr(row, field) != new_value:
                    setattr(row, field, new_value)
                    changed = True
    return changed


async def create_listing(
    session: AsyncSession, host_id: UUID, request: ListingCreate
) -> ListingDetail:
    values = request.model_dump(exclude={"amenity_ids", "hours", "booking_rules", "media"})
    listing = Listing(host_id=host_id, status=ListingStatus.PENDING, **values)
    session.add(listing)
    await session.flush()
    await set_amenities(session, listing.id, request.amenity_ids)
    if request.hours is not None:
        await set_week(session, listing.id, ListingHours, request.hours)
    if request.booking_rules is not None:
        await set_week(session, listing.id, ListingBookingRule, request.booking_rules)
    session.add_all(
        ListingMedia(listing_id=listing.id, **item.model_dump()) for item in request.media
    )
    return await finish(session, listing)


async def active_future_stays(session: AsyncSession, listing_id: UUID) -> list[Booking]:
    return list(
        (
            await session.scalars(
                select(Booking)
                .where(
                    Booking.listing_id == listing_id,
                    Booking.reservation_state == ReservationState.CONFIRMED,
                    Booking.departure_at > datetime.now(UTC),
                )
                .order_by(Booking.id)
            )
        ).all()
    )


async def patch_listing(
    session: AsyncSession, host_id: UUID, listing_id: UUID, request: ListingPatch
) -> ListingDetail:
    listing = await lock_listing(session, listing_id, host_id=host_id)
    ensure_mutable(listing)
    values = request.model_dump(exclude_unset=True)
    changed_fields = {
        field
        for field, value in values.items()
        if field != "amenity_ids" and getattr(listing, field) != value
    }
    if changed_fields & (LOCATION_FIELDS | {"max_guests"}):
        stays = await active_future_stays(session, listing.id)
        if stays and changed_fields & LOCATION_FIELDS:
            raise conflict(
                "Location and timezone cannot change while future/ongoing stays depend on them"
            )
        if any(stay.guests > values.get("max_guests", listing.max_guests) for stay in stays):
            raise conflict("Capacity cannot be reduced below a future/ongoing stay's guest count")
    if "amenity_ids" in values and await set_amenities(
        session, listing.id, values.pop("amenity_ids")
    ):
        changed_fields.add("amenity_ids")
    for field, value in values.items():
        setattr(listing, field, value)
    host_edit(
        listing, material=bool(changed_fields & MATERIAL_FIELDS), changed=bool(changed_fields)
    )
    if listing.status == ListingStatus.APPROVED:
        await ensure_complete(session, listing)
    return await finish(session, listing)


async def ensure_complete(session: AsyncSession, listing: Listing) -> None:
    missing = []
    try:
        ListingCreate.model_validate(
            {
                field: getattr(listing, field)
                for field in ListingCreate.model_fields
                if hasattr(listing, field)
            }
        )
    except ValidationError as exc:
        missing.extend(
            {"field": str(error["loc"][0]), "message": error["msg"]} for error in exc.errors()
        )
    for field in ("description", "contact_name", "contact_email", "contact_phone"):
        if not getattr(listing, field).strip():
            missing.append({"field": field, "message": "Required for approval"})
    media = (
        await session.scalars(select(ListingMedia).where(ListingMedia.listing_id == listing.id))
    ).all()
    if not any(item.media_type == MediaType.IMAGE for item in media):
        missing.append({"field": "media", "message": "At least one HTTPS photo is required"})
    for model, input_type, field in (
        (ListingHours, HoursInput, "hours"),
        (ListingBookingRule, BookingRuleInput, "booking_rules"),
    ):
        rows = (await session.scalars(select(model).where(model.listing_id == listing.id))).all()
        if {row.weekday for row in rows} != set(range(7)):
            missing.append({"field": field, "message": "All seven weekdays are required"})
        for row in rows:
            try:
                input_type.model_validate(
                    {key: getattr(row, key) for key in input_type.model_fields}
                )
            except ValidationError:
                missing.append({"field": field, "message": "Invalid weekly window"})
        if model is ListingBookingRule and not (
            any(row.arrival_allowed for row in rows) and any(row.departure_allowed for row in rows)
        ):
            missing.append({"field": field, "message": "Enable at least one arrival/departure day"})
    if missing:
        raise APIError(
            422, "LISTING_INCOMPLETE", "Listing is not complete for approval", details=missing
        )


async def replace_hours(session, host_id, listing_id, request) -> ListingDetail:
    listing = await lock_listing(session, listing_id, host_id=host_id)
    ensure_mutable(listing)
    changed = await set_week(session, listing.id, ListingHours, request.hours)
    host_edit(listing, changed=changed)
    return await finish(session, listing)


async def replace_rules(session, host_id, listing_id, request) -> ListingDetail:
    listing = await lock_listing(session, listing_id, host_id=host_id)
    ensure_mutable(listing)
    rules = {rule.weekday: rule for rule in request.booking_rules}
    timezone = ZoneInfo(listing.timezone)
    for stay in await active_future_stays(session, listing.id):
        for direction, accepted in (("arrival", stay.arrival_at), ("departure", stay.departure_at)):
            local = accepted.astimezone(timezone)
            rule = rules[local.weekday()]
            if not getattr(rule, f"{direction}_allowed") or not (
                getattr(rule, f"{direction}_start")
                <= local.time()
                <= getattr(rule, f"{direction}_end")
            ):
                raise conflict(
                    "Booking rules cannot invalidate a future/ongoing stay's accepted times"
                )
    changed = await set_week(session, listing.id, ListingBookingRule, request.booking_rules)
    host_edit(listing, changed=changed)
    if listing.status == ListingStatus.APPROVED:
        await ensure_complete(session, listing)
    return await finish(session, listing)


async def nested_row(session, model, listing_id: UUID, identifier: UUID):
    row = await session.scalar(
        select(model).where(model.id == identifier, model.listing_id == listing_id)
    )
    if row is None:
        raise APIError(404, "NOT_FOUND", "Resource not found")
    return row


async def add_media(session, host_id, listing_id, request: MediaInput) -> MediaResponse:
    listing = await lock_listing(session, listing_id, host_id=host_id)
    ensure_mutable(listing)
    count = await session.scalar(
        select(func.count()).select_from(ListingMedia).where(ListingMedia.listing_id == listing.id)
    )
    if count >= 30:
        raise conflict("A listing supports at most 30 media URLs")
    media = ListingMedia(listing_id=listing.id, **request.model_dump())
    session.add(media)
    host_edit(listing, material=True)
    await finish(session, listing)
    return MediaResponse.model_validate(media)


async def patch_media(session, host_id, listing_id, media_id, request: MediaPatch) -> MediaResponse:
    listing = await lock_listing(session, listing_id, host_id=host_id)
    ensure_mutable(listing)
    media = await nested_row(session, ListingMedia, listing.id, media_id)
    changed = False
    for field, value in request.model_dump(exclude_unset=True).items():
        if getattr(media, field) != value:
            setattr(media, field, value)
            changed = True
    host_edit(listing, material=True, changed=changed)
    await finish(session, listing)
    return MediaResponse.model_validate(media)


async def delete_media(session, host_id, listing_id, media_id):
    listing = await lock_listing(session, listing_id, host_id=host_id)
    ensure_mutable(listing)
    media = await nested_row(session, ListingMedia, listing.id, media_id)
    await session.delete(media)
    host_edit(listing, material=True)
    await finish(session, listing)


async def blocks_page(session, host_id, listing_id, page, page_size) -> Paginated[BlockResponse]:
    await get_listing(session, listing_id, host_id=host_id)
    condition = AvailabilityBlock.listing_id == listing_id
    total = await session.scalar(
        select(func.count()).select_from(AvailabilityBlock).where(condition)
    )
    blocks = (
        await session.scalars(
            select(AvailabilityBlock)
            .where(condition)
            .order_by(AvailabilityBlock.start_date, AvailabilityBlock.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return Paginated(
        data=[BlockResponse.model_validate(row) for row in blocks],
        pagination=pagination(page, page_size, total),
    )


async def add_block(session, host_id, listing_id, request: BlockInput) -> BlockResponse:
    listing = await lock_listing(session, listing_id, host_id=host_id)
    ensure_mutable(listing)
    reserved = await session.scalar(
        select(Booking.id)
        .where(
            Booking.listing_id == listing.id,
            Booking.reservation_state == ReservationState.CONFIRMED,
            Booking.check_in < request.end_date,
            Booking.check_out > request.start_date,
        )
        .limit(1)
    )
    blocked = await session.scalar(
        select(AvailabilityBlock.id)
        .where(
            AvailabilityBlock.listing_id == listing.id,
            AvailabilityBlock.start_date < request.end_date,
            AvailabilityBlock.end_date > request.start_date,
        )
        .limit(1)
    )
    if reserved or blocked:
        raise conflict(
            "Dates overlap a noncancelled reservation or an existing block", "DATES_UNAVAILABLE"
        )
    block = AvailabilityBlock(listing_id=listing.id, **request.model_dump())
    session.add(block)
    host_edit(listing)
    await finish(session, listing)
    return BlockResponse.model_validate(block)


async def delete_block(session, host_id, listing_id, block_id):
    listing = await lock_listing(session, listing_id, host_id=host_id)
    ensure_mutable(listing)
    block = await nested_row(session, AvailabilityBlock, listing.id, block_id)
    await session.delete(block)
    host_edit(listing)
    await finish(session, listing)


async def moderate(
    session, admin_id, listing_id, action: AdminActionType, reason=None
) -> ListingDetail:
    listing = await lock_listing(session, listing_id)
    ensure_mutable(listing)
    if listing.status != ListingStatus.PENDING:
        raise conflict("Only pending listings can be approved or rejected", "INVALID_LISTING_STATE")
    if action == AdminActionType.APPROVED:
        await ensure_complete(session, listing)
        listing.status = ListingStatus.APPROVED
    else:
        listing.status = ListingStatus.REJECTED
    listing.updated_at = datetime.now(UTC)
    session.add(AdminAction(admin_id=admin_id, listing_id=listing.id, action=action, reason=reason))
    return await finish(session, listing)


async def remove_listing(session, actor_id, listing_id, reason, *, host_id=None) -> ListingDetail:
    listing = await lock_listing(session, listing_id, host_id=host_id)
    if listing.status == ListingStatus.REMOVED:
        return await listing_detail(session, listing)
    now = datetime.now(UTC)
    listing.status = ListingStatus.REMOVED
    listing.removed_at = now
    listing.updated_at = now
    session.add(
        ListingRemoval(listing_id=listing.id, actor_id=actor_id, reason=reason, created_at=now)
    )
    if host_id is None:
        session.add(
            AdminAction(
                admin_id=actor_id,
                listing_id=listing.id,
                action=AdminActionType.REMOVED,
                reason=reason,
                created_at=now,
            )
        )
    return await finish(session, listing)


async def audit_page(session, page, page_size, listing_id=None) -> Paginated[AuditResponse]:
    filters = [AdminAction.listing_id == listing_id] if listing_id else []
    total = await session.scalar(select(func.count()).select_from(AdminAction).where(*filters))
    rows = (
        await session.scalars(
            select(AdminAction)
            .where(*filters)
            .order_by(AdminAction.created_at.desc(), AdminAction.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return Paginated(
        data=[AuditResponse.model_validate(row) for row in rows],
        pagination=pagination(page, page_size, total),
    )
