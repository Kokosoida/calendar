import calendar
import datetime
import enum
from typing import Literal, Optional, Union

from dateutil import rrule
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, conint


class Weekdays(str, enum.Enum):
    mon = "mon"
    tue = "tue"
    wed = "wed"
    thu = "thu"
    fri = "fri"
    sat = "sat"
    sun = "sun"


WEEKDAY_TO_INT = {wd: i for i, wd in enumerate(Weekdays, start=calendar.firstweekday())}


class MonthlyRecurrenceMode(str, enum.Enum):
    by_day = "by_day"
    by_weekday = "by_weekday"


class BaseRecurrenceSchema(BaseModel):
    interval: conint(ge=1)
    count: Optional[conint(ge=2)] = None
    until: Optional[datetime.datetime] = None


class DailyRecurrenceSchema(BaseRecurrenceSchema):
    type: Literal["daily"]

    def get_rrule(self, start: datetime.datetime):
        return rrule.rrule(
            freq=rrule.DAILY,
            dtstart=start,
            until=self.until,
            interval=self.interval,
            count=self.count,
        )


class WeeklyRecurrenceSchema(BaseRecurrenceSchema):
    type: Literal["weekly"]
    weekdays: set[Weekdays]

    def get_rrule(self, start: datetime.datetime):
        int_weekdays = [WEEKDAY_TO_INT[wd] for wd in self.weekdays]

        return rrule.rrule(
            freq=rrule.WEEKLY,
            dtstart=start,
            byweekday=int_weekdays,
            until=self.until,
            interval=self.interval,
            count=self.count,
        )


class MonthlyRecurrenceSchema(BaseRecurrenceSchema):
    type: Literal["monthly"]
    mode: MonthlyRecurrenceMode

    def get_rrule(self, start: datetime.datetime):
        if self.mode == MonthlyRecurrenceMode.by_day:
            return rrule.rrule(
                freq=rrule.MONTHLY,
                dtstart=start,
                until=self.until,
                interval=self.interval,
                count=self.count,
            )

        else:
            byweekday = rrule.weekday(start.weekday())((start.day - 1) // 7 + 1)
            return rrule.rrule(
                freq=rrule.MONTHLY,
                dtstart=start,
                byweekday=byweekday,
                until=self.until,
                interval=self.interval,
                count=self.count,
            )


class YearlyRecurrenceSchema(BaseRecurrenceSchema):
    type: Literal["yearly"]

    def get_rrule(self, start: datetime.datetime):
        return rrule.rrule(
            freq=rrule.YEARLY,
            dtstart=start,
            until=self.until,
            interval=self.interval,
            count=self.count,
        )


class RecurrenceSchema(BaseModel):
    description: Union[
        MonthlyRecurrenceSchema,
        WeeklyRecurrenceSchema,
        DailyRecurrenceSchema,
        YearlyRecurrenceSchema,
    ]

    def generate_for_timeperiod(
        self,
        after: datetime.datetime,
        before: datetime.datetime,
        start: datetime.datetime,
        duration_minutes: int,
    ):
        rule = self.description.get_rrule(start)
        # we have to use `after - duration_minutes` because if event starts before `after`
        # and ends after `after`, `between` won't generate it
        yield from rule.between(
            after - relativedelta(minutes=duration_minutes), before, inc=True
        )
