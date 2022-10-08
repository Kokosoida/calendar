import datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.orm.session import Session

from app.schemas.recurrence import RecurrenceSchema, Weekdays
from app.services.event import EventService
from tests.factories import (
    EventFactory,
    EventInviteFactory,
    WeeklyRecurrenceSchemaFactory,
)


class TestFindFreeSpot:
    @pytest.fixture(scope="class")
    def find_event_spot(self, async_loop):
        def run_find_event_spot(*args, **kwargs):
            return async_loop.run_until_complete(
                EventService().find_event_spot(*args, **kwargs)
            )

        return run_find_event_spot

    @pytest.fixture
    def small_spot_schedule(self, db: Session):
        recurrence = RecurrenceSchema(
            description=WeeklyRecurrenceSchemaFactory(
                weekdays={Weekdays.mon, Weekdays.tue}
            )
        )
        event_a = EventFactory(recurrence=recurrence, duration_minutes=60 * 24 - 10)

        recurrence = RecurrenceSchema(
            description=WeeklyRecurrenceSchemaFactory(
                weekdays={
                    Weekdays.wed,
                    Weekdays.thu,
                    Weekdays.fri,
                    Weekdays.sat,
                    Weekdays.sun,
                }
            )
        )
        event_b = EventFactory.create(
            recurrence=recurrence, duration_minutes=60 * 24 - 10
        )

        return event_a, event_b

    def test_small_spot(self, small_spot_schedule, find_event_spot):
        event_a, event_b = small_spot_schedule
        result = find_event_spot(
            user_ids={event_a.owner_id, event_b.owner_id},
            after=datetime.datetime(2022, 1, 2, 0, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 1, 20, 0, 0, tzinfo=ZoneInfo("UTC")),
            duration_minutes=11,
        )

        assert result is None

        result = find_event_spot(
            user_ids={event_a.owner_id, event_b.owner_id},
            after=datetime.datetime(2022, 1, 2, 0, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 1, 20, 0, 0, tzinfo=ZoneInfo("UTC")),
            duration_minutes=10,
        )

        assert result == datetime.datetime(2022, 1, 2, 23, 50, tzinfo=ZoneInfo("UTC"))

    def test_after_before(self, small_spot_schedule, find_event_spot):
        event_a, event_b = small_spot_schedule
        result = find_event_spot(
            user_ids={event_a.owner_id, event_b.owner_id},
            after=datetime.datetime(2022, 1, 2, 0, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 1, 2, 23, 30, tzinfo=ZoneInfo("UTC")),
            duration_minutes=1,
        )
        assert result is None

        result = find_event_spot(
            user_ids={event_a.owner_id, event_b.owner_id},
            after=datetime.datetime(2022, 1, 3, 0, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 1, 4, 0, 0, tzinfo=ZoneInfo("UTC")),
            duration_minutes=1,
        )
        assert result == datetime.datetime(2022, 1, 3, 23, 50, tzinfo=ZoneInfo("UTC"))

        result = find_event_spot(
            user_ids={event_a.owner_id, event_b.owner_id},
            after=datetime.datetime(2022, 1, 4, 23, 50, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 1, 4, 23, 51, tzinfo=ZoneInfo("UTC")),
            duration_minutes=1,
        )
        assert result == datetime.datetime(2022, 1, 4, 23, 50, tzinfo=ZoneInfo("UTC"))

    def test_no_events(self, user, find_event_spot):
        result = find_event_spot(
            user_ids={user.id},
            after=datetime.datetime(2022, 1, 2, 0, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 1, 20, 0, 0, tzinfo=ZoneInfo("UTC")),
            duration_minutes=10,
        )

        assert result == datetime.datetime(2022, 1, 2, 0, 0, tzinfo=ZoneInfo("UTC"))

    def test_event_starts_before_after(self, small_spot_schedule, find_event_spot):
        event_a, event_b = small_spot_schedule
        result = find_event_spot(
            user_ids={event_a.owner_id, event_b.owner_id},
            after=datetime.datetime(2022, 1, 1, 12, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 1, 2, 0, 0, tzinfo=ZoneInfo("UTC")),
            duration_minutes=1,
        )
        assert result == datetime.datetime(2022, 1, 1, 23, 50, tzinfo=ZoneInfo("UTC"))

    def test_event_no_recurrence(self, event, find_event_spot):
        result = find_event_spot(
            user_ids={event.owner_id},
            after=datetime.datetime(2022, 1, 1, 1, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 1, 2, 0, 0, tzinfo=ZoneInfo("UTC")),
            duration_minutes=1,
        )
        assert result == datetime.datetime(2022, 1, 1, 2, 0, tzinfo=ZoneInfo("UTC"))

    @pytest.fixture
    def events_with_invites(self, user):
        event_a = EventFactory(
            start=datetime.datetime(2022, 1, 1, 0, 0, tzinfo=ZoneInfo("UTC")),
            duration_minutes=10,
        )
        EventInviteFactory(event=event_a, user=user)

        event_b = EventFactory(
            start=datetime.datetime(2022, 1, 1, 0, 9, tzinfo=ZoneInfo("UTC")),
            duration_minutes=10,
        )
        EventInviteFactory(event=event_b, user=user)

        # Event invite to other user
        EventFactory(
            start=datetime.datetime(2022, 1, 1, 0, 18, tzinfo=ZoneInfo("UTC")),
            duration_minutes=10,
        )
        EventInviteFactory(event=event_b)

        EventFactory(
            start=datetime.datetime(2022, 1, 1, 0, 19, tzinfo=ZoneInfo("UTC")),
            duration_minutes=2,
            owner=user,
        )

    def test_invites(self, user, events_with_invites, find_event_spot):
        result = find_event_spot(
            user_ids={user.id},
            after=datetime.datetime(2022, 1, 1, 0, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 1, 2, 0, 0, tzinfo=ZoneInfo("UTC")),
            duration_minutes=5,
        )

        assert result == datetime.datetime(2022, 1, 1, 0, 21, tzinfo=ZoneInfo("UTC"))


class TestListEvents:
    @pytest.fixture(scope="class")
    def list_events(self, async_loop):
        def run_list_events(*args, **kwargs):
            return async_loop.run_until_complete(
                EventService().list_events_for_user(*args, **kwargs)
            )

        return run_list_events

    @pytest.fixture
    def events_with_invites(self, user):
        event_a = EventFactory(
            start=datetime.datetime(2022, 1, 1, 0, 0, tzinfo=ZoneInfo("UTC")),
            duration_minutes=10,
            name="event_a",
        )
        EventInviteFactory(event=event_a, user=user)

        event_b = EventFactory(
            start=datetime.datetime(2022, 1, 10, 0, 10, tzinfo=ZoneInfo("UTC")),
            duration_minutes=10,
            name="event_b",
        )
        EventInviteFactory(event=event_b, user=user)

        # Event invite to other user
        EventFactory(
            start=datetime.datetime(2022, 1, 1, 0, 18, tzinfo=ZoneInfo("UTC")),
            duration_minutes=10,
        )
        EventInviteFactory(event=event_b)

        # Event with recurrence
        recurrence = RecurrenceSchema(
            description=WeeklyRecurrenceSchemaFactory(
                weekdays={Weekdays.mon, Weekdays.tue}
            )
        )
        event_c = EventFactory(
            start=datetime.datetime(2022, 1, 1, 0, 19, tzinfo=ZoneInfo("UTC")),
            duration_minutes=2,
            owner=user,
            recurrence=recurrence,
            name="event_c",
        )
        return event_a, event_b, event_c

    def test_list(self, user, list_events, events_with_invites):
        result = list_events(
            user_id=user.id,
            after=datetime.datetime(2022, 1, 1, 0, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC")),
            event_id_gt=0,
        )
        events = tuple((e.name, e.occurrences) for e in result)

        assert events == (
            (
                "event_a",
                [datetime.datetime(2022, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)],
            ),
            (
                "event_b",
                [datetime.datetime(2022, 1, 10, 0, 10, tzinfo=datetime.timezone.utc)],
            ),
            (
                "event_c",
                [
                    datetime.datetime(2022, 1, 3, 0, 19, tzinfo=datetime.timezone.utc),
                    datetime.datetime(2022, 1, 4, 0, 19, tzinfo=datetime.timezone.utc),
                    datetime.datetime(2022, 1, 10, 0, 19, tzinfo=datetime.timezone.utc),
                    datetime.datetime(2022, 1, 11, 0, 19, tzinfo=datetime.timezone.utc),
                ],
            ),
        )

        result = list_events(
            user_id=user.id,
            after=datetime.datetime(2022, 1, 10, 0, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC")),
            event_id_gt=0,
        )
        events = tuple((e.name, e.occurrences) for e in result)

        assert events == (
            (
                "event_b",
                [datetime.datetime(2022, 1, 10, 0, 10, tzinfo=datetime.timezone.utc)],
            ),
            (
                "event_c",
                [
                    datetime.datetime(2022, 1, 10, 0, 19, tzinfo=datetime.timezone.utc),
                    datetime.datetime(2022, 1, 11, 0, 19, tzinfo=datetime.timezone.utc),
                ],
            ),
        )

    def test_after(self, user, list_events, events_with_invites):
        event_a, _, _ = events_with_invites
        result = list_events(
            user_id=user.id,
            after=datetime.datetime(2022, 1, 1, 0, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 1, 11, 0, 0, tzinfo=ZoneInfo("UTC")),
            event_id_gt=event_a.id,
        )
        events = tuple((e.name, e.occurrences) for e in result)

        assert events == (
            (
                "event_b",
                [datetime.datetime(2022, 1, 10, 0, 10, tzinfo=datetime.timezone.utc)],
            ),
            (
                "event_c",
                [
                    datetime.datetime(2022, 1, 3, 0, 19, tzinfo=datetime.timezone.utc),
                    datetime.datetime(2022, 1, 4, 0, 19, tzinfo=datetime.timezone.utc),
                    datetime.datetime(2022, 1, 10, 0, 19, tzinfo=datetime.timezone.utc),
                ],
            ),
        )

    def test_empty(self, user, list_events, events_with_invites):
        _, _, event_c = events_with_invites
        result = list_events(
            user_id=user.id,
            after=datetime.datetime(2021, 1, 1, 0, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2021, 1, 11, 0, 0, tzinfo=ZoneInfo("UTC")),
            event_id_gt=0,
        )
        assert result == []

        result = list_events(
            user_id=user.id,
            after=datetime.datetime(2022, 1, 1, 0, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 1, 11, 0, 0, tzinfo=ZoneInfo("UTC")),
            event_id_gt=event_c.id,
        )
        assert result == []
