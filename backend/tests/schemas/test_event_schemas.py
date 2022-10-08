import datetime
from zoneinfo import ZoneInfo

import pytest

from app.schemas.recurrence import MonthlyRecurrenceMode, RecurrenceSchema


class TestDailyRecurrence:
    def test_timezone(self, daily_recurrence_schema):
        schema = RecurrenceSchema(description=daily_recurrence_schema)

        result = schema.generate_for_timeperiod(
            after=datetime.datetime(2022, 1, 1, 12, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 1, 3, 12, 0, tzinfo=ZoneInfo("UTC")),
            start=datetime.datetime(
                2022, 1, 1, 12, 0, tzinfo=ZoneInfo("Europe/Moscow")
            ),
            duration_minutes=1,
        )

        assert list(result) == [
            datetime.datetime(2022, 1, 2, 12, 0, tzinfo=ZoneInfo("Europe/Moscow")),
            datetime.datetime(2022, 1, 3, 12, 0, tzinfo=ZoneInfo("Europe/Moscow")),
        ]

    @pytest.mark.parametrize("daily_recurrence_schema__interval", [3])
    def test_increment(self, daily_recurrence_schema):
        schema = RecurrenceSchema(description=daily_recurrence_schema)

        result = schema.generate_for_timeperiod(
            after=datetime.datetime(2022, 1, 1, 12, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 1, 9, 12, 0, tzinfo=ZoneInfo("UTC")),
            start=datetime.datetime(2022, 1, 1, 12, 0, tzinfo=ZoneInfo("UTC")),
            duration_minutes=1,
        )

        assert list(result) == [
            datetime.datetime(2022, 1, 1, 12, 0, tzinfo=ZoneInfo("UTC")),
            datetime.datetime(2022, 1, 4, 12, 0, tzinfo=ZoneInfo("UTC")),
            datetime.datetime(2022, 1, 7, 12, 0, tzinfo=ZoneInfo("UTC")),
        ]


class TestWeeklyRecurrence:
    @pytest.mark.parametrize("weekly_recurrence_schema__interval", [2])
    def test_interval(self, weekly_recurrence_schema):
        schema = RecurrenceSchema(description=weekly_recurrence_schema)

        result = schema.generate_for_timeperiod(
            after=datetime.datetime(2022, 1, 4, 12, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 1, 30, 12, 0, tzinfo=ZoneInfo("UTC")),
            start=datetime.datetime(2022, 1, 3, 12, 0, tzinfo=ZoneInfo("UTC")),
            duration_minutes=1,
        )

        assert list(result) == [
            datetime.datetime(2022, 1, 4, 12, 0, tzinfo=ZoneInfo("UTC")),
            datetime.datetime(2022, 1, 17, 12, 0, tzinfo=ZoneInfo("UTC")),
            datetime.datetime(2022, 1, 18, 12, 0, tzinfo=ZoneInfo("UTC")),
        ]

    @pytest.mark.parametrize("weekly_recurrence_schema__count", [3])
    def test_count(self, weekly_recurrence_schema):
        schema = RecurrenceSchema(description=weekly_recurrence_schema)

        result = schema.generate_for_timeperiod(
            after=datetime.datetime(2022, 1, 4, 12, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 1, 30, 12, 0, tzinfo=ZoneInfo("UTC")),
            start=datetime.datetime(2022, 1, 3, 12, 0, tzinfo=ZoneInfo("UTC")),
            duration_minutes=1,
        )

        assert list(result) == [
            datetime.datetime(2022, 1, 4, 12, 0, tzinfo=ZoneInfo("UTC")),
            datetime.datetime(2022, 1, 10, 12, 0, tzinfo=ZoneInfo("UTC")),
        ]

    @pytest.mark.parametrize(
        "weekly_recurrence_schema__until",
        [datetime.datetime(2022, 1, 9, 12, 0, tzinfo=ZoneInfo("UTC"))],
    )
    def test_until(self, weekly_recurrence_schema):
        schema = RecurrenceSchema(description=weekly_recurrence_schema)

        result = schema.generate_for_timeperiod(
            after=datetime.datetime(2022, 1, 4, 12, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 1, 30, 12, 0, tzinfo=ZoneInfo("UTC")),
            start=datetime.datetime(2022, 1, 3, 12, 0, tzinfo=ZoneInfo("UTC")),
            duration_minutes=1,
        )

        assert list(result) == [
            datetime.datetime(2022, 1, 4, 12, 0, tzinfo=ZoneInfo("UTC")),
        ]


class TestMonthlyRecurrence:
    def test_by_day(self, monthly_recurrence_schema):
        schema = RecurrenceSchema(description=monthly_recurrence_schema)

        result = schema.generate_for_timeperiod(
            after=datetime.datetime(2022, 1, 2, 12, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 4, 20, 12, 0, tzinfo=ZoneInfo("UTC")),
            start=datetime.datetime(2022, 1, 1, 12, 0, tzinfo=ZoneInfo("UTC")),
            duration_minutes=1,
        )

        assert list(result) == [
            datetime.datetime(2022, 2, 1, 12, 0, tzinfo=ZoneInfo("UTC")),
            datetime.datetime(2022, 3, 1, 12, 0, tzinfo=ZoneInfo("UTC")),
            datetime.datetime(2022, 4, 1, 12, 0, tzinfo=ZoneInfo("UTC")),
        ]

    def test_by_day_31st(self, monthly_recurrence_schema):
        schema = RecurrenceSchema(description=monthly_recurrence_schema)

        result = schema.generate_for_timeperiod(
            after=datetime.datetime(2022, 1, 1, 12, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 4, 20, 12, 0, tzinfo=ZoneInfo("UTC")),
            start=datetime.datetime(2022, 1, 31, 12, 0, tzinfo=ZoneInfo("UTC")),
            duration_minutes=1,
        )

        assert list(result) == [
            datetime.datetime(2022, 1, 31, 12, 0, tzinfo=ZoneInfo("UTC")),
            datetime.datetime(2022, 3, 31, 12, 0, tzinfo=ZoneInfo("UTC")),
        ]

    @pytest.mark.parametrize(
        "monthly_recurrence_schema__mode", [MonthlyRecurrenceMode.by_weekday]
    )
    def test_by_weekday(self, monthly_recurrence_schema):
        schema = RecurrenceSchema(description=monthly_recurrence_schema)

        result = schema.generate_for_timeperiod(
            after=datetime.datetime(2022, 2, 1, 12, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2022, 5, 1, 12, 0, tzinfo=ZoneInfo("UTC")),
            start=datetime.datetime(2022, 1, 4, 12, 0, tzinfo=ZoneInfo("UTC")),
            duration_minutes=1,
        )

        assert list(result) == [
            datetime.datetime(2022, 2, 1, 12, 0, tzinfo=ZoneInfo("UTC")),
            datetime.datetime(2022, 3, 1, 12, 0, tzinfo=ZoneInfo("UTC")),
            datetime.datetime(2022, 4, 5, 12, 0, tzinfo=ZoneInfo("UTC")),
        ]


class TestYearlyRecurrence:
    def test_ok(self, yearly_recurrence_schema):
        schema = RecurrenceSchema(description=yearly_recurrence_schema)
        result = schema.generate_for_timeperiod(
            after=datetime.datetime(2022, 1, 1, 12, 0, tzinfo=ZoneInfo("UTC")),
            before=datetime.datetime(2024, 1, 1, 12, 0, tzinfo=ZoneInfo("UTC")),
            start=datetime.datetime(2022, 5, 1, 12, 0, tzinfo=ZoneInfo("UTC")),
            duration_minutes=1,
        )

        assert list(result) == [
            datetime.datetime(2022, 5, 1, 12, 0, tzinfo=ZoneInfo("UTC")),
            datetime.datetime(2023, 5, 1, 12, 0, tzinfo=ZoneInfo("UTC")),
        ]
