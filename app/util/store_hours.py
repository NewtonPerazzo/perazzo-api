from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

DAY_KEYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

WEEKDAY_TO_KEY = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday",
}


def default_business_hours() -> dict:
    return {
        day: {
            "enabled": False,
            "start_time": None,
            "end_time": None,
        }
        for day in DAY_KEYS
    }


def normalize_business_hours(value: dict | None) -> dict:
    result = default_business_hours()
    if not value:
        return result

    for day in DAY_KEYS:
        raw = value.get(day) if isinstance(value, dict) else None
        if not isinstance(raw, dict):
            continue

        enabled = bool(raw.get("enabled", False))
        start_time = _normalize_time(raw.get("start_time"))
        end_time = _normalize_time(raw.get("end_time"))

        result[day] = {
            "enabled": enabled,
            "start_time": start_time,
            "end_time": end_time,
        }

    return result


def validate_business_hours(hours: dict) -> None:
    for day in DAY_KEYS:
        item = hours.get(day) if isinstance(hours, dict) else None
        if not isinstance(item, dict):
            continue

        enabled = bool(item.get("enabled", False))
        start_time = _normalize_time(item.get("start_time"))
        end_time = _normalize_time(item.get("end_time"))

        if enabled and (not start_time or not end_time):
            raise ValueError(f"{day} requires start_time and end_time when enabled")

        if start_time and end_time:
            start = _parse_time(start_time)
            end = _parse_time(end_time)
            if start >= end:
                raise ValueError(f"{day} start_time must be before end_time")


def is_open_now(hours: dict | None, now: datetime | None = None) -> bool:
    current = now or datetime.now(ZoneInfo("America/Sao_Paulo"))
    normalized = normalize_business_hours(hours)
    day_key = WEEKDAY_TO_KEY[current.weekday()]
    item = normalized.get(day_key, {})

    if not bool(item.get("enabled", False)):
        return False

    start_time = _normalize_time(item.get("start_time"))
    end_time = _normalize_time(item.get("end_time"))
    if not start_time or not end_time:
        return False

    start = _parse_time(start_time)
    end = _parse_time(end_time)
    now_time = current.time().replace(second=0, microsecond=0)
    return start <= now_time <= end


def _normalize_time(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    _parse_time(text)
    return text


def _parse_time(value: str) -> time:
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as exc:
        raise ValueError(f"Invalid time format: {value}") from exc

