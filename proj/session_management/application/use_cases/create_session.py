from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from ..dto.session_dto import session_to_dto
from ..ports import EventPublisherPort
from ...domain.entities.session import Session as DomainSession
from ...domain.value_objects.time_window import TimeWindow
from ...domain.value_objects.location import Location


def _parse_iso(dt_str: str) -> datetime:
    # accept trailing Z
    if dt_str.endswith("Z"):
        dt_str = dt_str[:-1] + "+00:00"
    return datetime.fromisoformat(dt_str)


class CreateSessionUseCase:
    def __init__(self, repository, service, publisher: Optional[EventPublisherPort] = None):
        self.repo = repository
        self.service = service
        self.publisher = publisher

    def execute(self, auth_lecturer_id: int, payload: dict) -> dict:
        # Build TimeWindow and Location value objects
        start = _parse_iso(payload["time_created"]) if isinstance(payload.get("time_created"), str) else payload.get("time_created")
        end = _parse_iso(payload["time_ended"]) if isinstance(payload.get("time_ended"), str) else payload.get("time_ended")
        tw = TimeWindow(start=start, end=end)

        loc = Location(latitude=float(payload["latitude"]), longitude=float(payload["longitude"]), description=payload.get("location_description"))

        # Lecturer identity enforced from auth (do not accept lecturer_id in payload)
        session = DomainSession(
            session_id=None,
            program_id=int(payload["program_id"]),
            course_id=int(payload["course_id"]),
            lecturer_id=int(auth_lecturer_id),
            stream_id=payload.get("stream_id"),
            date_created=tw.start.date(),
            time_window=tw,
            location=loc,
        )

        saved = self.service.create_session(session)

        # publish event (best-effort)
        if self.publisher:
            try:
                self.publisher.publish("session.created", {"session_id": saved.session_id, "program_id": saved.program_id, "stream_id": saved.stream_id})
            except Exception:
                # do not fail use-case on publisher errors
                pass

        return session_to_dto(saved)
