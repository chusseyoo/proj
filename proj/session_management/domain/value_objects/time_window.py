from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

try:
    from django.utils import timezone as dj_timezone  # type: ignore
    def _now():
        return dj_timezone.now()
    def _ensure_tz(dt: datetime) -> datetime:
        return dj_timezone.make_aware(dt) if dt.tzinfo is None else dt
except Exception:
    def _now():
        return datetime.now(timezone.utc)
    def _ensure_tz(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt


# Canonical bounds per proj_docs README: 30 minutes to 3 hours
MIN_DURATION = timedelta(minutes=30)
MAX_DURATION = timedelta(hours=3)


@dataclass(frozen=True)
class TimeWindow:
    start: datetime
    end: datetime

    def __post_init__(self):
        start = _ensure_tz(self.start)
        end = _ensure_tz(self.end)
        if end <= start:
            raise ValueError("time window end must be after start")
        duration = end - start
        if duration < MIN_DURATION or duration > MAX_DURATION:
            raise ValueError(f"duration must be between {MIN_DURATION} and {MAX_DURATION}")
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)

    def contains(self, instant: datetime) -> bool:
        instant = _ensure_tz(instant)
        return self.start <= instant < self.end

    def overlaps(self, other: "TimeWindow") -> bool:
        return self.start < other.end and other.start < self.end
