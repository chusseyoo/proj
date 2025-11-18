from __future__ import annotations

from datetime import datetime
from typing import Optional

from ..dto.session_dto import session_to_dto
from ...domain.value_objects.time_window import TimeWindow
from ...domain.value_objects.location import Location


class UpdateSessionUseCase:
    def __init__(self, repository, service=None):
        self.repo = repository
        self.service = service

    def execute(self, auth_lecturer_id: int, session_id: int, updates: dict) -> dict:
        session = self.repo.get_by_id(session_id)
        if session.lecturer_id != auth_lecturer_id:
            raise PermissionError("Not owner of session")

        # Apply updates: allow time window and location updates
        start = updates.get("time_created", session.time_window.start)
        end = updates.get("time_ended", session.time_window.end)
        if isinstance(start, str):
            if start.endswith("Z"):
                start = start[:-1] + "+00:00"
            start = datetime.fromisoformat(start)
        if isinstance(end, str):
            if end.endswith("Z"):
                end = end[:-1] + "+00:00"
            end = datetime.fromisoformat(end)

        new_tw = TimeWindow(start=start, end=end)

        loc = session.location
        if "latitude" in updates or "longitude" in updates or "location_description" in updates:
            lat = float(updates.get("latitude", loc.latitude))
            lon = float(updates.get("longitude", loc.longitude))
            desc = updates.get("location_description", getattr(loc, "description", None))
            loc = Location(latitude=lat, longitude=lon, description=desc)

        new_session = session.__class__(
            session_id=session.session_id,
            program_id=session.program_id,
            course_id=session.course_id,
            lecturer_id=session.lecturer_id,
            stream_id=updates.get("stream_id", session.stream_id),
            date_created=session.date_created,
            time_window=new_tw,
            location=loc,
        )

        saved = self.repo.save(new_session)
        return session_to_dto(saved)
