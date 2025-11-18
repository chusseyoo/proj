from __future__ import annotations

from ..dto.session_dto import session_to_dto


class GetSessionUseCase:
    def __init__(self, repository, service=None):
        self.repo = repository
        self.service = service

    def execute(self, auth_lecturer_id: int, session_id: int) -> dict:
        session = self.repo.get_by_id(session_id)
        if session.lecturer_id != auth_lecturer_id:
            raise PermissionError("Not owner of session")
        return session_to_dto(session)
