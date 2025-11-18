from __future__ import annotations

from datetime import datetime, timezone
from typing import Tuple

from ..domain.value_objects.time_window import MIN_DURATION, MAX_DURATION
from .exceptions import CommandValidationError


def parse_iso(dt) -> datetime:
    """Parse a value into a timezone-aware datetime (UTC if naive).

    Accepts datetime or ISO string (with optional trailing Z).
    Raises CommandValidationError on invalid input.
    """
    if isinstance(dt, datetime):
        d = dt
    elif isinstance(dt, str):
        if dt.endswith("Z"):
            dt = dt[:-1] + "+00:00"
        try:
            d = datetime.fromisoformat(dt)
        except Exception as exc:
            raise CommandValidationError(f"invalid ISO datetime: {dt}") from exc
    else:
        raise CommandValidationError("datetime must be a string or datetime instance")

    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d


def validate_lat_lon(lat, lon) -> Tuple[float, float]:
    """Coerce and validate latitude/longitude values.

    Returns (lat, lon) as floats. Raises CommandValidationError on invalid ranges.
    """
    try:
        latf = float(lat)
        lonf = float(lon)
    except Exception:
        raise CommandValidationError("latitude and longitude must be numeric")

    if not (-90.0 <= latf <= 90.0):
        raise CommandValidationError("latitude must be between -90 and 90")
    if not (-180.0 <= lonf <= 180.0):
        raise CommandValidationError("longitude must be between -180 and 180")
    return latf, lonf


def validate_time_window_bounds(start: datetime, end: datetime) -> None:
    """Ensure duration between start and end is within MIN_DURATION and MAX_DURATION.

    Raises CommandValidationError if invalid.
    """
    if end <= start:
        raise CommandValidationError("time_ended must be after time_created")
    duration = end - start
    if duration < MIN_DURATION or duration > MAX_DURATION:
        raise CommandValidationError(f"duration must be between {MIN_DURATION} and {MAX_DURATION}")
