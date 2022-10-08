import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, conint, conset, root_validator

from app.core.config import settings
from app.schemas.event import IntervalSchema


class FindFreeSpotRequestParams(IntervalSchema):
    duration_minutes: conint(ge=1, le=settings.MAX_EVENT_DURATION_MINUTES)
    user_ids: conset(uuid.UUID, max_items=100)

    @root_validator
    def validate_before_after(cls, values):
        if "before" not in values or "after" not in values:
            return values

        delta = (values["before"] - values["after"]) / datetime.timedelta(minutes=1)

        if delta > cls.Config.MAX_DELTA:
            raise ValueError(
                f"after-before interval should not exceed {settings.MAX_INTERVAL_DURATION_MINUTES} minutes"
            )

        if "duration_minutes" in values and delta < values["duration_minutes"]:
            raise ValueError("`before` must be greater than `after + duration_minutes`")
        elif delta <= 0:
            raise ValueError("`before` must be greater than `after`")

        return values

    class Config:
        MAX_DELTA = settings.MAX_INTERVAL_DURATION_MINUTES


class FindFreeSpotResponse(BaseModel):
    timeslot: Optional[datetime.datetime]
