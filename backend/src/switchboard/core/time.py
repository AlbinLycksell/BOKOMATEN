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


def to_utc_aware(dt: datetime) -> datetime:
    """Normalize a possibly-naive datetime to UTC-aware.

    SQLite returns naive datetimes from ``DateTime`` columns even though
    we store UTC. When mixing freshly-assigned ``utcnow()`` (aware) with
    a value just read from the DB (naive), subtraction raises
    ``TypeError: can't subtract offset-naive and offset-aware datetimes``.
    Always pass DB-loaded timestamps through this helper before arithmetic.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)
