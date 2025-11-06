"""Assign Lecturer to Course use case."""

from typing import Optional

from ....domain.exceptions import (
    CourseNotFoundError,
    LecturerNotFoundError,
    LecturerInactiveError,
    ValidationError
)
from ....infrastructure.repositories import CourseRepository
from ...dto import CourseDTO, to_course_dto


class AssignLecturerUseCase:
    """Use case for assigning a lecturer to a course."""

    def __init__(self, course_repository: CourseRepository):
        """Initialize use case with repository dependency.
        
        Args:
            course_repository: Repository for course data access
        """
        self.course_repository = course_repository

    def execute(
        self,
        course_id: int,
        lecturer_id: int,
        include_program_code: bool = False
    ) -> CourseDTO:
        """Assign a lecturer to a course.
        
        Args:
            course_id: ID of the course
            lecturer_id: ID of the lecturer to assign
            include_program_code: Whether to include program_code in DTO
            
        Returns:
            CourseDTO with updated course data and lecturer_name
            
        Raises:
            CourseNotFoundError: If course does not exist
            LecturerNotFoundError: If lecturer does not exist
            LecturerInactiveError: If lecturer account is not active
        """
        # Retrieve course
        course = self.course_repository.find_by_id(course_id)
        if course is None:
            raise CourseNotFoundError(f"Course with ID {course_id} not found")
        
        # Validate lecturer exists and is active (cross-context)
        self._validate_lecturer(lecturer_id)
        
        # Assign lecturer by updating only the lecturer_id field
        updated_course = self.course_repository.update(course_id, {'lecturer_id': lecturer_id})
        
        # Enrichment
        program_code = None
        if include_program_code:
            from ....infrastructure.repositories import ProgramRepository
            program_repository = ProgramRepository()
            program = program_repository.find_by_id(updated_course.program_id)
            if program:
                program_code = program.program_code
        
        lecturer_name = self._get_lecturer_name(lecturer_id)
        
        return to_course_dto(
            updated_course,
            program_code=program_code,
            lecturer_name=lecturer_name
        )

    def _validate_lecturer(self, lecturer_id: int) -> None:
        """Validate lecturer exists and is active (cross-context).
        
        Raises:
            LecturerNotFoundError: If lecturer doesn't exist
            LecturerInactiveError: If lecturer account is not active
        """
        from user_management.infrastructure.orm.django_models import LecturerProfile
        
        try:
            lecturer_profile = LecturerProfile.objects.select_related('user').get(
                lecturer_id=lecturer_id
            )
        except LecturerProfile.DoesNotExist:
            raise LecturerNotFoundError(f"Lecturer with ID {lecturer_id} not found")
        
        if not lecturer_profile.user.is_active:
            raise LecturerInactiveError(
                f"Lecturer account for ID {lecturer_id} is not active"
            )

    def _get_lecturer_name(self, lecturer_id: int) -> Optional[str]:
        """Get lecturer full name (cross-context)."""
        from user_management.infrastructure.orm.django_models import LecturerProfile
        
        try:
            lecturer_profile = LecturerProfile.objects.select_related('user').get(
                lecturer_id=lecturer_id
            )
            return lecturer_profile.user.get_full_name()
        except LecturerProfile.DoesNotExist:
            return None
