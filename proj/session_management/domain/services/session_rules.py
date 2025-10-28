from __future__ import annotations

from typing import List

from ..entities.session import Session
from ..ports import (
    SessionRepositoryPort,
    AcademicStructurePort,
    UserManagementPort,
)
from ..exceptions import OverlappingSessionError, LecturerNotAssignedError, StreamMismatchError


class SessionService:
    """Service implementing creation and domain-level policies for Session."""

    def __init__(
        self,
        repository: SessionRepositoryPort,
        academic_port: AcademicStructurePort,
        user_port: UserManagementPort,
    ):
        self._repo = repository
        self._academic = academic_port
        self._users = user_port

    def create_session(self, session: Session) -> Session:
        # check overlapping sessions for lecturer
        if self._repo.has_overlapping(session.lecturer_id, session.time_window):
            raise OverlappingSessionError("Lecturer has overlapping session")

        # Validate program/course consistency
        if not self._academic.course_belongs_to_program(session.course_id, session.program_id):
            raise StreamMismatchError("Course does not belong to program")

        # Validate program/stream targeting
        if not self._academic.program_has_streams(session.program_id) and session.stream_id is not None:
            raise StreamMismatchError("Program does not support streams but stream_id was provided")

        if session.stream_id is not None and not self._academic.stream_belongs_to_program(
            session.stream_id, session.program_id
        ):
            raise StreamMismatchError("Stream does not belong to program")

        # Validate lecturer assignment and status
        assigned_lecturer = self._academic.get_course_lecturer(session.course_id)
        if assigned_lecturer != session.lecturer_id:
            raise LecturerNotAssignedError("Lecturer is not assigned to the course")

        if not self._users.is_lecturer_active(session.lecturer_id):
            raise LecturerNotAssignedError("Lecturer account is not active")

        saved = self._repo.save(session)
        return saved

    def get_eligible_students(self, session: Session) -> List[int]:
        return self._repo.get_eligible_students(session)
