from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from ..value_objects.time_window import TimeWindow
from ..value_objects.location import Location


@dataclass(frozen=True)
class Session:
    session_id: Optional[int]
    program_id: int
    course_id: int
    lecturer_id: int
    stream_id: Optional[int]
    date_created: date
    time_window: TimeWindow
    location: Location

    @property
    def is_active(self) -> bool:
        try:
            from django.utils import timezone

            now = timezone.now()
        except Exception:
            from datetime import datetime, timezone as _tz

            now = datetime.now(_tz.utc)

        return self.time_window.start <= now < self.time_window.end

    @property
    def has_ended(self) -> bool:
        try:
            from django.utils import timezone

            now = timezone.now()
        except Exception:
            from datetime import datetime, timezone as _tz

            now = datetime.now(_tz.utc)

        return now >= self.time_window.end
