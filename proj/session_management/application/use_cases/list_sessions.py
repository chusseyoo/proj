from __future__ import annotations

from datetime import datetime
from typing import Optional

from ..dto.session_dto import session_to_dto


class ListMySessionsUseCase:
    def __init__(self, repository, service=None):
        self.repo = repository
        self.service = service

    def execute(self, auth_lecturer_id: int, *, program_id: Optional[int] = None, course_id: Optional[int] = None, stream_id: Optional[int] = None, start: Optional[datetime] = None, end: Optional[datetime] = None, page: int = 1, page_size: int = 20):
        # For now use repository list_by_lecturer and do simple pagination in-memory
        sessions = self.repo.list_by_lecturer(auth_lecturer_id, start=start, end=end)

        # apply optional filters
        if program_id is not None:
            sessions = [s for s in sessions if s.program_id == program_id]
        if course_id is not None:
            sessions = [s for s in sessions if s.course_id == course_id]
        if stream_id is not None:
            sessions = [s for s in sessions if s.stream_id == stream_id]

        total = len(sessions)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_items = sessions[start_idx:end_idx]

        return {
            "results": [session_to_dto(s) for s in page_items],
            "total_count": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "has_next": end_idx < total,
            "has_previous": start_idx > 0,
        }
