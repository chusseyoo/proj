from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Dict


def session_to_dto(session) -> Dict:
    """Convert a domain Session entity to a simple dict DTO."""
    try:
        status = "active" if session.is_active else ("ended" if session.has_ended else "created")
    except Exception:
        status = "created"

    return {
        "session_id": session.session_id,
        "program_id": session.program_id,
        "course_id": session.course_id,
        "lecturer_id": session.lecturer_id,
        "stream_id": session.stream_id,
        "time_created": session.time_window.start.isoformat(),
        "time_ended": session.time_window.end.isoformat(),
        "latitude": str(session.location.latitude),
        "longitude": str(session.location.longitude),
        "location_description": getattr(session.location, "description", None),
        "status": status,
    }
