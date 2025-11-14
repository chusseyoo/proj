"""
ProfileService: student/lecturer profile retrieval and updates.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from ...domain.exceptions import (
    StudentNotFoundError,
    LecturerNotFoundError,
    StreamNotAllowedError,
    StreamRequiredError,
    StreamNotInProgramError,
    InvalidYearError,
)
from ...domain.services import EnrollmentService
from ...infrastructure.repositories import (
    StudentProfileRepository,
    LecturerProfileRepository,
)
from academic_structure.infrastructure.orm.django_models import Stream as StreamModel


@dataclass
class ProfileService:
    student_repository: StudentProfileRepository
    lecturer_repository: LecturerProfileRepository

    def get_student_profile(self, student_profile_id: int) -> Dict:
        profile = self.student_repository.get_with_full_info(student_profile_id)
        return {'student_profile': profile}

    def get_student_profile_by_user_id(self, user_id: int) -> Dict:
        profile = self.student_repository.get_by_user_id(user_id)
        return {'student_profile': profile}

    def get_student_profile_by_student_id(self, student_id: str) -> Dict:
        profile = self.student_repository.get_by_student_id(student_id.strip().upper())
        return {'student_profile': profile}

    def update_student_profile(self, student_profile_id: int, update_data: Dict) -> Dict:
        profile = self.student_repository.get_by_id(student_profile_id)

        if 'stream_id' in update_data:
            stream_id = update_data['stream_id']
            program_has_streams = self._program_has_streams(profile.program_id)
            EnrollmentService.validate_stream_requirement(program_has_streams, stream_id)
            if stream_id is not None:
                self._ensure_stream_in_program(stream_id, profile.program_id)

        if 'year_of_study' in update_data:
            EnrollmentService.validate_year_of_study(update_data['year_of_study'])

        updated = self.student_repository.update(student_profile_id, **update_data)
        return {'student_profile': updated}

    def get_lecturer_profile(self, lecturer_id: int) -> Dict:
        profile = self.lecturer_repository.get_with_user(lecturer_id)
        return {'lecturer_profile': profile}

    def get_lecturer_profile_by_user_id(self, user_id: int) -> Dict:
        profile = self.lecturer_repository.get_by_user_id(user_id)
        return {'lecturer_profile': profile}

    def update_lecturer_profile(self, lecturer_id: int, update_data: Dict) -> Dict:
        if 'department_name' in update_data:
            name = (update_data['department_name'] or '').strip()
            if len(name) < 3:
                raise ValueError('Department name must be at least 3 characters')
            update_data['department_name'] = name
        updated = self.lecturer_repository.update(lecturer_id, **update_data)
        return {'lecturer_profile': updated}

    # Helpers
    def _program_has_streams(self, program_id: int) -> bool:
        # Avoid cross-context repo for now; query via ORM
        from academic_structure.infrastructure.orm.django_models import Program as ProgramModel
        try:
            program = ProgramModel.objects.get(program_id=program_id)
        except ProgramModel.DoesNotExist:
            # Treat as no streams if not found; could raise ProgramNotFoundError if desired
            return False
        return program.has_streams

    def _ensure_stream_in_program(self, stream_id: int, program_id: int) -> None:
        try:
            stream = StreamModel.objects.get(id=stream_id)
        except StreamModel.DoesNotExist:
            raise StreamNotInProgramError('Stream does not belong to program')
        if stream.program_id != program_id:
            raise StreamNotInProgramError('Stream does not belong to program')
