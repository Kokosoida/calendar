import datetime

from dateutil.relativedelta import relativedelta
from fastapi_users_db_sqlalchemy import GUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import BigInteger, DateTime, Integer, Text

from app.db import Base
from app.deps.db import PydanticType
from app.schemas.recurrence import RecurrenceSchema


class Event(Base):
    __tablename__ = "event"

    id = Column(BigInteger, primary_key=True)
    owner_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="events")
    name = Column(Text, nullable=False)

    created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    start = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    recurrence = Column(PydanticType(RecurrenceSchema), nullable=True)

    invites = relationship(
        "EventInvite", back_populates="event", cascade="all, delete-orphan"
    )

    def generate_for_timeperiod(
        self, after: datetime.datetime, before: datetime.datetime
    ):
        if self.start > before:
            return

        if self.recurrence:
            # TODO: fix auto conversion to pydantic for some reason not working
            recurrence = RecurrenceSchema(**self.recurrence)
            yield from recurrence.generate_for_timeperiod(
                after, before, self.start, self.duration_minutes
            )
            return

        if (
            self.start >= after
            or self.start + relativedelta(minutes=self.duration_minutes) >= after
        ):
            yield self.start
