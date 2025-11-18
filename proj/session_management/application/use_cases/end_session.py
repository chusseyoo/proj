from __future__ import annotations

from datetime import datetime, timezone, timedelta

from ..dto.session_dto import session_to_dto
from ...domain.value_objects.time_window import TimeWindow, MIN_DURATION


class EndSessionUseCase:
    def __init__(self, repository, service=None):
        self.repo = repository
        self.service = service

    def execute(self, auth_lecturer_id: int, session_id: int, now: datetime | None = None) -> dict:
        if now is None:
            now = datetime.now(timezone.utc)

        session = self.repo.get_by_id(session_id)
        if session.lecturer_id != auth_lecturer_id:
            raise PermissionError("Not owner of session")

        # compute new end: at least now, and not before start+MIN_DURATION
        start = session.time_window.start
        min_end = start + MIN_DURATION
        new_end = max(now, min_end)

        new_tw = TimeWindow(start=start, end=new_end)

        new_session = session.__class__(
            session_id=session.session_id,
            program_id=session.program_id,
            course_id=session.course_id,
            lecturer_id=session.lecturer_id,
            stream_id=session.stream_id,
            date_created=session.date_created,
            time_window=new_tw,
            location=session.location,
        )

        saved = self.repo.save(new_session)
        return session_to_dto(saved)
