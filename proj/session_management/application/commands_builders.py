from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict

from .commands_queries import CreateSessionCommand
from .exceptions import CommandValidationError
from .validators import parse_iso, validate_lat_lon, validate_time_window_bounds


def build_create_session_command(payload: Dict[str, Any]) -> CreateSessionCommand:
    """Build a CreateSessionCommand from a raw dict (e.g. parsed JSON).

    Performs basic type coercion and validation. Deeper domain validations
    (e.g., TimeWindow duration bounds, lecturer/course relations) are left to
    domain services and value objects.
    """
    required = ["program_id", "course_id", "time_created", "time_ended", "latitude", "longitude"]
    missing = [k for k in required if k not in payload]
    if missing:
        raise CommandValidationError(f"missing required fields: {', '.join(missing)}")

    program_id = int(payload["program_id"]) if payload.get("program_id") is not None else None
    course_id = int(payload["course_id"]) if payload.get("course_id") is not None else None
    stream_id = payload.get("stream_id")
    if stream_id is not None:
        stream_id = int(stream_id)

    time_created = parse_iso(payload["time_created"])
    time_ended = parse_iso(payload["time_ended"])
    # validate duration bounds
    validate_time_window_bounds(time_created, time_ended)

    # validate and coerce lat/lon
    latf, lonf = validate_lat_lon(payload["latitude"], payload["longitude"])
    # keep DTO string shape for compatibility with existing use-cases
    latitude = str(latf)
    longitude = str(lonf)

    location_description = payload.get("location_description")

    cmd = CreateSessionCommand(
        program_id=program_id,
        course_id=course_id,
        stream_id=stream_id,
        time_created=time_created,
        time_ended=time_ended,
        latitude=latitude,
        longitude=longitude,
        location_description=location_description,
    )
    return cmd
