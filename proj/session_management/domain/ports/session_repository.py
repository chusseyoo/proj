from __future__ import annotations

from typing import Protocol, List, Optional

from ..entities.session import Session
from ..value_objects.time_window import TimeWindow


class SessionRepositoryPort(Protocol):
    """Repository port required by domain services for persistence and queries."""

    def save(self, session: Session) -> Session:
        ...

    def get(self, session_id: int) -> Optional[Session]:
        ...

    def list_by_lecturer(self, lecturer_id: int, *, start: Optional[str] = None, end: Optional[str] = None) -> List[Session]:
        ...

    def has_overlapping(self, lecturer_id: int, time_window: TimeWindow) -> bool:
        ...

    def get_eligible_students(self, session: Session) -> List[int]:
        ...
