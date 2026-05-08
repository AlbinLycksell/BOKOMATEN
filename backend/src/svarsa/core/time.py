from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

STOCKHOLM = ZoneInfo("Europe/Stockholm")


def utcnow() -> datetime:
    return datetime.now(UTC)


def now_se() -> datetime:
    return datetime.now(STOCKHOLM)


def to_se(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(STOCKHOLM)
