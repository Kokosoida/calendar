from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic.error_wrappers import ErrorWrapper
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import joinedload

from app.deps.db import get_async_session
from app.deps.users import current_user
from app.models import EventInvite
from app.models.event import Event
from app.models.user import User
from app.schemas.event import (
    EventCreateSchema,
    EventInviteSchema,
    EventListRequestSchema,
    EventListResponseSchema,
    EventSchema,
    InviteUpdateSchema,
)
from app.schemas.free_spot import FindFreeSpotRequestParams, FindFreeSpotResponse
from app.services.event import EventService

router = APIRouter(prefix="/events")


async def validate_user_ids(user_ids, session, field_name):
    """
    Validate that all user_ids exist in db.

    TODO: filter only active users
    """
    db_users = await session.execute(select(User.id).filter(User.id.in_(user_ids)))
    db_user_ids = set([user.id for user in db_users])
    incorrect_user_ids = user_ids - db_user_ids

    if incorrect_user_ids:
        raise RequestValidationError(
            [
                ErrorWrapper(
                    ValueError(
                        f"users {[str(u) for u in incorrect_user_ids]} do not exist"
                    ),
                    loc=field_name,
                )
            ]
        )


@router.post("", response_model=EventSchema, status_code=201)
async def create_event(
    item_in: EventCreateSchema,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    """
    Create an event with all the information:

    - **start**: start time of event
    - **duration_minutes**: event duration in minutes
    - **recurrence**: recurrence params of event
    - **invitee_ids**: list of user ids invited to event
    """

    await validate_user_ids(item_in.invitee_ids, session, "invitee_ids")

    event_kwargs = {**item_in.dict(), "owner_id": user.id}
    invitee_ids = event_kwargs.pop("invitee_ids")
    event = Event(**event_kwargs)

    invitee_ids -= {user.id}

    event.invites = [
        EventInvite(event=event, user_id=invitee_id) for invitee_id in invitee_ids
    ]

    session.add(event)
    await session.commit()
    # TODO: there should be a better way to do it other than `event.__dict__`
    return event


@router.post("/find-free-spot", response_model=FindFreeSpotResponse, status_code=200)
async def find_free_spot(
    request_params: FindFreeSpotRequestParams,
    event_service: EventService = Depends(EventService),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Find free spot for event in schedule:

    - **after**: start time of interval to search
    - **before**: end time of interval to search
    - **duration_minutes**: event duration
    - **user_ids**: list of user ids to check for availability


    - **before** must be greater than **after** + **duration_minutes**
    - **after** and **before** must not include seconds and milliseconds, must include timezone info

    """
    await validate_user_ids(request_params.user_ids, session, "user_ids")

    timeslot = await event_service.find_event_spot(**request_params.dict())
    return {"timeslot": timeslot}


@router.get("", response_model=EventListResponseSchema)
async def get_events(
    request_params: EventListRequestSchema = Depends(),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    """
    List events for current user.

    - **before** must be greater than **after**
    - **after** and **before** must not include seconds and milliseconds, must include timezone info

    Response is paginated. To request next batch use offset provided in response.
    offset=null means there are no more events.
    """
    events_with_occurrences = await EventService().list_events_for_user(
        user_id=user.id,
        after=request_params.after,
        before=request_params.before,
        event_id_gt=request_params.offset,
    )

    events_with_occurrences = sorted(events_with_occurrences, key=lambda e: e.id)

    offset_is_needed = len(events_with_occurrences) > request_params.limit
    events_with_occurrences = events_with_occurrences[: request_params.limit]

    return {
        "events_with_occurrences": events_with_occurrences,
        "offset": events_with_occurrences[-1].id if offset_is_needed else None,
    }


@router.patch("/{event_id}/invite", response_model=EventInviteSchema)
async def accept_event(
    event_id: int,
    invite_in: InviteUpdateSchema,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    invite: Optional[EventInvite] = (
        await session.scalars(
            select(EventInvite).filter(
                EventInvite.event_id == event_id, EventInvite.user_id == user.id
            )
        )
    ).first()

    if not invite:
        raise HTTPException(404)

    invite.is_accepted = invite_in.is_accepted
    session.add(invite)
    await session.commit()
    return invite


@router.get("/{event_id}", response_model=EventSchema)
async def get_event(
    event_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    event: Optional[Event] = (
        await session.scalars(
            select(Event)
            .filter(Event.id == event_id)
            .options(joinedload(Event.invites))
        )
    ).first()
    if not event:
        raise HTTPException(404)

    return event


@router.delete("/{event_id}")
async def delete_event(
    event_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    item: Optional[Event] = await session.get(Event, event_id)

    if not item or item.owner_id != user.id:
        raise HTTPException(404)

    await session.delete(item)
    await session.commit()
    return {"success": True}
