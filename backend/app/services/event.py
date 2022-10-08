import datetime
import uuid
from typing import Iterable

from bitarray import bitarray
from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.deps.db import get_async_session
from app.models import Event, EventInvite
from app.schemas.event import EventWithOccurrencesSchema


class FreeSpotFinder:
    """
    Finder of free spots in schedule of multiple events.

    Works by iterating over events and removing occupied spots from bitarray.
    """

    def __init__(
        self, after: datetime.datetime, before: datetime.datetime, duration: int
    ):
        self.after = after
        self.before = before
        self.duration = duration
        self.bitarray = None

    def find(self, events: Iterable[Event]):
        self.init_array()

        for event in events:
            for event_start in event.generate_for_timeperiod(self.after, self.before):
                self.remove_event_from_array(event_start, event.duration_minutes)

        return self.find_spot_in_array()

    def init_array(self):
        self.bitarray = bitarray(
            self.get_diff_in_minutes(
                self.before - relativedelta(minutes=self.duration - 1), self.after
            )
        )
        self.bitarray.setall(0)

    def remove_event_from_array(self, start: datetime.datetime, duration_minutes: int):
        bias = self.get_diff_in_minutes(start, self.after)
        if bias < 0:
            duration_minutes += bias
            bias = 0

        self.bitarray[bias : bias + duration_minutes] = 1

    def find_spot_in_array(self):
        """Return free spot start_time in bitarray."""
        current_len = 0
        start = None

        for i, val in enumerate(self.bitarray):
            if val == 0:
                if start is None:
                    start = i
                current_len += 1
            else:
                start = None
                current_len = 0

            if current_len == self.duration:
                break
        else:
            return None

        return self.after + relativedelta(minutes=start)

    def get_diff_in_minutes(self, dt1: datetime.datetime, dt2: datetime.datetime):
        return int((dt1 - dt2).total_seconds()) // 60


class EventService:
    async def find_event_spot(
        self,
        user_ids: set[uuid.UUID],
        after: datetime.datetime,
        before: datetime.datetime,
        duration_minutes: int,
    ):
        assert before > after

        async for session in get_async_session():

            events = (
                await session.execute(
                    self.get_event_query_for_user_ids(user_ids, before)
                )
            ).scalars()

            spot_finder = FreeSpotFinder(after, before, duration_minutes)
            return spot_finder.find(events)

    async def list_events_for_user(
        self,
        user_id: uuid.UUID,
        after: datetime.datetime,
        before: datetime.datetime,
        event_id_gt: int,
    ) -> list[EventWithOccurrencesSchema]:
        async for session in get_async_session():

            # TODO: find a way to load smaller set of events from DB
            events = (
                (
                    await session.execute(
                        self.get_event_query_for_user_ids({user_id}, before)
                        .filter(Event.id > event_id_gt)
                        .order_by("id")
                        .options(joinedload(Event.invites))
                    )
                )
                .unique()
                .scalars()
            )

            events_with_occurrences = []

            for event in events:
                event_occurrences = []

                for event_start in event.generate_for_timeperiod(after, before):
                    event_occurrences.append(event_start)

                if event_occurrences:
                    event.occurrences = event_occurrences
                    events_with_occurrences.append(
                        EventWithOccurrencesSchema.from_orm(event)
                    )

            return events_with_occurrences

    def get_event_query_for_user_ids(self, user_ids, before):
        """Return query for selecting event for specified user_ids."""
        # TODO: filter only is_active events here
        return (
            select(Event)
            .filter(
                Event.owner_id.in_(user_ids)
                | Event.id.in_(
                    select(EventInvite.event_id)
                    .filter(
                        EventInvite.user_id.in_(user_ids),
                        EventInvite.is_accepted == True,
                    )
                    .distinct()
                ),
                Event.start <= before,
            )
            .distinct()
        )
