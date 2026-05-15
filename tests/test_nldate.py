from datetime import date

import pytest

from nldate import parse

TODAY = date(2026, 5, 14)


def test_today_yesterday_tomorrow() -> None:
    assert parse("today", today=TODAY) == TODAY
    assert parse("yesterday", today=TODAY) == date(2026, 5, 13)
    assert parse("tomorrow", today=TODAY) == date(2026, 5, 15)


def test_next_weekday() -> None:
    assert parse("next Tuesday", today=TODAY) == date(2026, 5, 19)


def test_last_weekday() -> None:
    assert parse("last Monday", today=TODAY) == date(2026, 5, 11)


def test_bare_weekday_means_next_occurrence() -> None:
    assert parse("Thursday", today=TODAY) == date(2026, 5, 21)


def test_absolute_month_day_year() -> None:
    assert parse("December 1st, 2025", today=TODAY) == date(2025, 12, 1)


def test_absolute_day_month_year() -> None:
    assert parse("1 December 2025", today=TODAY) == date(2025, 12, 1)


def test_iso_date() -> None:
    assert parse("2025-12-01", today=TODAY) == date(2025, 12, 1)


def test_slash_date() -> None:
    assert parse("12/1/2025", today=TODAY) == date(2025, 12, 1)


def test_days_before_absolute_date() -> None:
    assert parse("5 days before December 1st, 2025", today=TODAY) == date(
        2025, 11, 26
    )


def test_compound_duration_after_yesterday() -> None:
    assert parse("1 year and 2 months after yesterday", today=TODAY) == date(
        2027, 7, 13
    )


def test_words_duration_from_tomorrow() -> None:
    assert parse("two weeks from tomorrow", today=TODAY) == date(2026, 5, 29)


def test_in_duration() -> None:
    assert parse("in 3 days", today=TODAY) == date(2026, 5, 17)


def test_ago_duration() -> None:
    assert parse("three weeks ago", today=TODAY) == date(2026, 4, 23)


def test_month_end_clamps() -> None:
    assert parse("1 month after January 31, 2025", today=TODAY) == date(2025, 2, 28)


def test_unparseable_input_raises_value_error() -> None:
    with pytest.raises(ValueError):
        parse("not a date", today=TODAY)

