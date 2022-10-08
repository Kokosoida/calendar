import datetime
from random import randint
from zoneinfo import ZoneInfo

import factory
from factory.alchemy import SESSION_PERSISTENCE_COMMIT

from app.models import Event, EventInvite, User
from app.schemas.recurrence import (
    DailyRecurrenceSchema,
    MonthlyRecurrenceMode,
    MonthlyRecurrenceSchema,
    Weekdays,
    WeeklyRecurrenceSchema,
    YearlyRecurrenceSchema,
)

session = None


class BaseRecurrenceFactory(factory.Factory):
    interval = 1
    count = None
    until = None


class DailyRecurrenceSchemaFactory(BaseRecurrenceFactory):
    class Meta:
        model = DailyRecurrenceSchema

    type = "daily"


class WeeklyRecurrenceSchemaFactory(BaseRecurrenceFactory):
    class Meta:
        model = WeeklyRecurrenceSchema

    weekdays = {Weekdays.mon, Weekdays.tue}
    type = "weekly"


class MonthlyRecurrenceSchemaFactory(BaseRecurrenceFactory):
    class Meta:
        model = MonthlyRecurrenceSchema

    mode = MonthlyRecurrenceMode.by_day
    type = "monthly"


class YearlyRecurrenceSchemaFactory(BaseRecurrenceFactory):
    class Meta:
        model = YearlyRecurrenceSchema

    type = "yearly"


class BaseModelFactory(factory.alchemy.SQLAlchemyModelFactory):
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        cls._meta.sqlalchemy_session = session
        return super()._create(model_class, *args, **kwargs)

    class Meta:
        sqlalchemy_session_persistence = SESSION_PERSISTENCE_COMMIT


class UserFactory(BaseModelFactory):
    class Meta:
        model = User

    email = factory.Faker("email")
    hashed_password = ""


class EventFactory(BaseModelFactory):
    class Meta:
        model = Event

    name = factory.LazyFunction(lambda: f"event_{randint(1, 10_000)}")
    owner = factory.SubFactory(UserFactory)
    start = datetime.datetime(2022, 1, 1, 0, 0, tzinfo=ZoneInfo("UTC"))
    duration_minutes = 120
    recurrence = None


class EventInviteFactory(BaseModelFactory):
    class Meta:
        model = EventInvite

    event = factory.SubFactory(EventFactory)
    user = factory.SubFactory(UserFactory)
    is_accepted = True
