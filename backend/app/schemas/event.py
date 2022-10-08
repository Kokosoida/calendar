import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, conint, conset, constr, validator

from app.core.config import settings
from app.schemas.recurrence import RecurrenceSchema


def validate_dt(dt: datetime.datetime):
    if not dt.tzinfo:
        raise ValueError("must contain timezone info")

    if not (dt.second == 0):
        raise ValueError("seconds must be 0")

    if not dt.microsecond == 0:
        raise ValueError("microseconds must be 0")
    return dt


class IntervalSchema(BaseModel):
    after: datetime.datetime
    before: datetime.datetime

    _validate_before = validator("before", allow_reuse=True)(validate_dt)
    _validate_after = validator("after", allow_reuse=True)(validate_dt)

    class Config:
        MAX_DELTA = None


class EventBaseSchema(BaseModel):
    start: datetime.datetime
    name: constr(min_length=1)
    duration_minutes: conint(ge=1, le=settings.MAX_EVENT_DURATION_MINUTES)
    recurrence: Optional[RecurrenceSchema] = None


class EventCreateSchema(EventBaseSchema):
    invitee_ids: conset(uuid.UUID, max_items=100)


class EventListRequestSchema(IntervalSchema):
    offset: int = 0
    limit: conint(ge=1, le=50) = 10


class EventUpdateSchema(EventCreateSchema):
    pass


class EventInviteSchema(BaseModel):
    user_id: uuid.UUID
    is_accepted: Optional[bool]

    class Config:
        orm_mode = True


class InviteUpdateSchema(BaseModel):
    is_accepted: Optional[bool]

    class Config:
        orm_mode = True


class EventSchema(EventBaseSchema):
    id: int
    owner_id: uuid.UUID
    invites: list[EventInviteSchema]

    class Config:
        orm_mode = True


class EventWithOccurrencesSchema(EventSchema):
    occurrences: list[datetime.datetime]

    class Config:
        orm_mode = True


class EventListResponseSchema(BaseModel):
    events_with_occurrences: list[EventWithOccurrencesSchema]
    offset: Optional[int]
