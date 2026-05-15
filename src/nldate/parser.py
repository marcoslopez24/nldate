from __future__ import annotations

import re
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta


class DateParseError(ValueError):
    """Raised when a natural-language date cannot be parsed."""


MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

MONTH_NAMES = "|".join(sorted(MONTHS, key=len, reverse=True))

WEEKDAYS = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "tues": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}

NUMBER_WORDS = {
    "zero": 0,
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "couple": 2,
    "few": 3,
    "hundred": 100,
    "thousand": 1000,
}

UNIT_ALIASES = {
    "d": "days",
    "day": "days",
    "days": "days",
    "fortnight": "weeks",
    "fortnights": "weeks",
    "wk": "weeks",
    "wks": "weeks",
    "week": "weeks",
    "weeks": "weeks",
    "mo": "months",
    "mos": "months",
    "month": "months",
    "months": "months",
    "yr": "years",
    "yrs": "years",
    "year": "years",
    "years": "years",
}

_NUMBER_PATTERN = r"\d+|[a-z]+(?:[- ][a-z]+)?"
_DURATION_RE = re.compile(
    rf"(?P<num>{_NUMBER_PATTERN})\s+"
    r"(?P<unit>fortnights?|days?|weeks?|months?|years?|wks?|mos?|yrs?|d)"
)


@dataclass(frozen=True)
class Duration:
    days: int = 0
    weeks: int = 0
    months: int = 0
    years: int = 0

    def signed(self, sign: int) -> Duration:
        return Duration(
            days=self.days * sign,
            weeks=self.weeks * sign,
            months=self.months * sign,
            years=self.years * sign,
        )


def parse(s: str, today: date | None = None) -> date:
    """Parse a common English date expression into a date."""
    reference = date.today() if today is None else today
    text = _normalize(s)
    if not text:
        msg = "cannot parse an empty date expression"
        raise DateParseError(msg)

    simple = _parse_simple(text, reference)
    if simple is not None:
        return simple

    relative = _parse_relative(text, reference)
    if relative is not None:
        return relative

    absolute = _parse_absolute(text, reference)
    if absolute is not None:
        return absolute

    msg = f"could not parse date expression: {s!r}"
    raise DateParseError(msg)


def _normalize(s: str) -> str:
    text = s.strip().lower()
    text = re.sub(r"\bnow\b", "today", text)
    text = re.sub(r"(?<=[a-z])-(?=[a-z])", " ", text)
    text = re.sub(r"\b(\d+)(st|nd|rd|th)\b", r"\1", text)
    text = re.sub(r"[,.!?]", "", text)
    text = re.sub(r"\bthe\b", " ", text)
    text = re.sub(r"\bof\b", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_simple(text: str, today: date) -> date | None:
    if text in {"today", "this day"}:
        return today
    if text == "yesterday":
        return today - timedelta(days=1)
    if text == "tomorrow":
        return today + timedelta(days=1)
    if text in {"day after tomorrow", "tomorrow after tomorrow"}:
        return today + timedelta(days=2)
    if text in {"day before yesterday", "yesterday before yesterday"}:
        return today - timedelta(days=2)
    return None


def _parse_relative(text: str, today: date) -> date | None:
    weekday = _parse_weekday_relative(text, today)
    if weekday is not None:
        return weekday

    simple_unit = _parse_simple_unit_relative(text, today)
    if simple_unit is not None:
        return simple_unit

    for marker, sign in (
        (" before ", -1),
        (" after ", 1),
        (" from ", 1),
        (" since ", 1),
    ):
        if marker in text:
            duration_text, base_text = text.split(marker, 1)
            duration = _parse_duration(duration_text)
            if duration is None:
                continue
            base = parse(base_text, today)
            return _add_duration(base, duration.signed(sign))

    for marker, sign in (
        (" plus ", 1),
        (" minus ", -1),
    ):
        if marker in text:
            base_text, duration_text = text.split(marker, 1)
            duration = _parse_duration(duration_text)
            if duration is None:
                continue
            base = parse(base_text, today)
            return _add_duration(base, duration.signed(sign))

    ago_match = re.fullmatch(r"(?P<duration>.+) ago", text)
    if ago_match is not None:
        duration = _parse_duration(ago_match.group("duration"))
        if duration is not None:
            return _add_duration(today, duration.signed(-1))

    earlier_later_match = re.fullmatch(r"(?P<duration>.+) (earlier|later)", text)
    if earlier_later_match is not None:
        duration = _parse_duration(earlier_later_match.group("duration"))
        if duration is not None:
            sign = -1 if earlier_later_match.group(2) == "earlier" else 1
            return _add_duration(today, duration.signed(sign))

    in_match = re.fullmatch(r"in (?P<duration>.+)", text)
    if in_match is not None:
        duration = _parse_duration(in_match.group("duration"))
        if duration is not None:
            return _add_duration(today, duration)

    return None


def _parse_weekday_relative(text: str, today: date) -> date | None:
    match = re.fullmatch(r"(next|last|this)? ?([a-z]+)", text)
    if match is None:
        return None
    modifier, weekday_text = match.groups()
    weekday = WEEKDAYS.get(weekday_text)
    if weekday is None:
        return None

    current = today.weekday()
    if modifier == "last":
        delta = (current - weekday) % 7
        return today - timedelta(days=delta or 7)
    if modifier == "this":
        return today + timedelta(days=(weekday - current) % 7)
    delta = (weekday - current) % 7
    return today + timedelta(days=delta or 7)


def _parse_simple_unit_relative(text: str, today: date) -> date | None:
    match = re.fullmatch(r"(next|last) (day|week|month|year)", text)
    if match is None:
        return None
    modifier, unit = match.groups()
    sign = 1 if modifier == "next" else -1
    if unit == "day":
        duration = Duration(days=sign)
    elif unit == "week":
        duration = Duration(weeks=sign)
    elif unit == "month":
        duration = Duration(months=sign)
    else:
        duration = Duration(years=sign)
    return _add_duration(today, duration)


def _parse_absolute(text: str, today: date) -> date | None:
    iso_match = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if iso_match is not None:
        iso_year, iso_month, iso_day = (int(part) for part in iso_match.groups())
        return date(iso_year, iso_month, iso_day)

    numeric_dash_match = re.fullmatch(r"(\d{1,2})-(\d{1,2})(?:-(\d{2,4}))?", text)
    if numeric_dash_match is not None:
        month, day, year_text = numeric_dash_match.groups()
        year = _year_from_text(year_text, today)
        return date(year, int(month), int(day))

    slash_match = re.fullmatch(r"(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?", text)
    if slash_match is not None:
        month, day, year_text = slash_match.groups()
        year = _year_from_text(year_text, today)
        return date(year, int(month), int(day))

    month_day = re.fullmatch(
        rf"({MONTH_NAMES}) (\d{{1,2}})(?: (\d{{2,4}}))?|"
        rf"(\d{{1,2}}) ({MONTH_NAMES})(?: (\d{{2,4}}))?",
        text,
    )
    if month_day is not None:
        first_month, first_day, first_year, second_day, second_month, second_year = (
            month_day.groups()
        )
        month_text = first_month or second_month
        day_text = first_day or second_day
        year_text = first_year or second_year
        if month_text is None or day_text is None:
            return None
        month = MONTHS.get(month_text)
        if month is None:
            return None
        year = _year_from_text(year_text, today)
        return date(year, month, int(day_text))

    return None


def _year_from_text(year_text: str | None, today: date) -> int:
    if year_text is None:
        return today.year
    year = int(year_text)
    if year < 100:
        return 2000 + year
    return year


def _parse_duration(text: str) -> Duration | None:
    cleaned = re.sub(r"\band\b", " ", text)
    cleaned = re.sub(r"\ba\b", "one", cleaned)
    cleaned = re.sub(r"\ban\b", "one", cleaned)
    matches = list(_DURATION_RE.finditer(cleaned))
    if not matches:
        return None

    totals = {"days": 0, "weeks": 0, "months": 0, "years": 0}
    covered = " ".join(match.group(0) for match in matches)
    if _normalize(covered) != _normalize(cleaned):
        return None

    for match in matches:
        value = _parse_number(match.group("num"))
        unit = UNIT_ALIASES[match.group("unit")]
        if match.group("unit") in {"fortnight", "fortnights"}:
            value *= 2
        totals[unit] += value

    return Duration(**totals)


def _parse_number(text: str) -> int:
    if text.isdigit():
        return int(text)
    words = text.replace("-", " ").split()
    total = 0
    current = 0
    for word in words:
        value = NUMBER_WORDS.get(word)
        if value is None:
            msg = f"unknown number word: {text!r}"
            raise DateParseError(msg)
        if value >= 100:
            current = max(current, 1) * value
        else:
            current += value
    total += current
    return total


def _add_duration(start: date, duration: Duration) -> date:
    shifted = _add_months(start, duration.years * 12 + duration.months)
    return shifted + timedelta(days=duration.days + duration.weeks * 7)


def _add_months(start: date, months: int) -> date:
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, monthrange(year, month)[1])
    return date(year, month, day)
