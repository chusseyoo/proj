from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from .dto.session_dto import session_to_dto
from ..domain.entities.session import Session as DomainSession
from ..domain.value_objects.time_window import TimeWindow
from ..domain.value_objects.location import Location


class InMemoryEventPublisher:
    def __init__(self):
        self.events: List[Dict] = []

    def publish(self, name: str, payload: Dict):
        # record events for assertions
        self.events.append({"name": name, "payload": payload})


class InMemoryAcademicPort:
    """Simple stub that accepts any program/course/stream relationships needed by tests."""

    def __init__(self, course_lecturer_map: Optional[Dict[int, int]] = None, programs_with_streams: Optional[set] = None):
        # map course_id -> lecturer_id
        self.course_lecturer_map = course_lecturer_map or {}
        self.programs_with_streams = programs_with_streams or set()

    def program_has_streams(self, program_id: int) -> bool:
        return program_id in self.programs_with_streams

    def stream_belongs_to_program(self, stream_id: int, program_id: int) -> bool:
        # for tests assume any stream id that equals program_id * 10 + n belongs
        return True

    def course_belongs_to_program(self, course_id: int, program_id: int) -> bool:
        return True

    def get_course_lecturer(self, course_id: int) -> int:
        return self.course_lecturer_map.get(course_id, 1)


class InMemoryUserPort:
    def __init__(self, active_lecturers: Optional[set] = None):
        self.active_lecturers = active_lecturers or set()

    def is_lecturer_active(self, lecturer_id: int) -> bool:
        # default to True unless explicitly absent from active_lecturers when non-empty
        if self.active_lecturers:
            return lecturer_id in self.active_lecturers
        return True


class InMemorySessionRepository:
    def __init__(self):
        self._store: Dict[int, DomainSession] = {}
        self._next = 1

    def save(self, session: DomainSession) -> DomainSession:
        # assign id if needed and store an immutable copy
        sid = session.session_id or self._next
        self._next = max(self._next, sid + 1)
        saved = session.__class__(
            session_id=sid,
            program_id=session.program_id,
            course_id=session.course_id,
            lecturer_id=session.lecturer_id,
            stream_id=session.stream_id,
            date_created=session.date_created,
            time_window=session.time_window,
            location=session.location,
        )
        self._store[sid] = saved
        return saved

    def get_by_id(self, session_id: int) -> DomainSession:
        # application layer uses repo.get_by_id naming in some places
        return self._store[session_id]

    # Port compatibility
    def get(self, session_id: int) -> Optional[DomainSession]:
        return self._store.get(session_id)

    def get_by_id_or_raise(self, session_id: int) -> DomainSession:
        return self.get(session_id)

    def list_by_lecturer(self, lecturer_id: int, *, start: Optional[datetime] = None, end: Optional[datetime] = None) -> List[DomainSession]:
        items = [s for s in self._store.values() if s.lecturer_id == lecturer_id]
        if start is not None:
            items = [s for s in items if s.time_window.end > start]
        if end is not None:
            items = [s for s in items if s.time_window.start < end]
        # sort by start
        items.sort(key=lambda s: s.time_window.start)
        return items

    def has_overlapping(self, lecturer_id: int, time_window: TimeWindow) -> bool:
        for s in self._store.values():
            if s.lecturer_id != lecturer_id:
                continue
            if s.time_window.overlaps(time_window):
                return True
        return False

    def get_eligible_students(self, session: DomainSession) -> List[int]:
        # simple stub: return empty list
        return []
