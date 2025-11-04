"""Create Course use case."""

from typing import Dict, Any, Optional

from ....domain.exceptions import (
    CourseCodeAlreadyExistsError,
    ProgramNotFoundError,
    LecturerNotFoundError,
    LecturerInactiveError,
    ValidationError
)
from ....infrastructure.repositories import CourseRepository, ProgramRepository
from ...dto import CourseDTO, to_course_dto


class CreateCourseUseCase:
    """Use case for creating a new course."""

    def __init__(
        self,
        course_repository: CourseRepository,
        program_repository: ProgramRepository
    ):
        """Initialize use case with repository dependencies.
        
        Args:
            course_repository: Repository for course data access
            program_repository: Repository for program data access
        """
        self.course_repository = course_repository
        self.program_repository = program_repository

    def execute(self, data: Dict[str, Any]) -> CourseDTO:
        """Create a new course.
        
        Args:
            data: Dictionary with course data:
                - course_code (str): Unique course code (e.g., "CS201")
                - course_name (str): Name of the course (3-200 chars)
                - program_id (int): Parent program ID
                - department_name (str): Department teaching the course
                - lecturer_id (int, optional): Assigned lecturer ID
                
        Returns:
            CourseDTO with created course data
            
        Raises:
            ValidationError: If input data is invalid
            ProgramNotFoundError: If program does not exist
            CourseCodeAlreadyExistsError: If course_code already exists
            LecturerNotFoundError: If lecturer_id provided but doesn't exist
            LecturerInactiveError: If lecturer account is not active
        """
        # Validate required fields
        required_fields = ['course_code', 'course_name', 'program_id', 'department_name']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Extract and normalize data
        course_code = data['course_code'].upper().strip()
        course_name = data['course_name'].strip()
        program_id = data['program_id']
        department_name = data['department_name'].strip()
        lecturer_id = data.get('lecturer_id')  # Optional
        
        # Validate course_code format (e.g., CS201, ENG301)
        if not self._is_valid_course_code(course_code):
            raise ValidationError(
                f"course_code must match pattern (2-4 uppercase letters + 3 digits), got: '{course_code}'"
            )
        
        # Validate course_name length
        if len(course_name) < 3 or len(course_name) > 200:
            raise ValidationError(
                f"course_name must be between 3 and 200 characters, got: {len(course_name)}"
            )
        
        # Validate department_name length
        if len(department_name) < 3 or len(department_name) > 150:
            raise ValidationError(
                f"department_name must be between 3 and 150 characters, got: {len(department_name)}"
            )
        
        # Check uniqueness
        if self.course_repository.exists_by_code(course_code):
            raise CourseCodeAlreadyExistsError(
                f"Course with code '{course_code}' already exists"
            )
        
        # Validate program exists
        program = self.program_repository.get_by_id(program_id)
        if program is None:
            raise ProgramNotFoundError(f"Program with ID {program_id} not found")
        
        # Validate lecturer if provided (cross-context)
        if lecturer_id is not None:
            self._validate_lecturer(lecturer_id)
        
        # Create course via repository
        course_data = {
            'course_code': course_code,
            'course_name': course_name,
            'program_id': program_id,
            'department_name': department_name,
            'lecturer_id': lecturer_id,
        }
        
        course = self.course_repository.create(course_data)
        
        # Optional enrichment
        lecturer_name = None
        if lecturer_id:
            lecturer_name = self._get_lecturer_name(lecturer_id)
        
        return to_course_dto(
            course,
            program_code=program.program_code,
            lecturer_name=lecturer_name
        )

    def _is_valid_course_code(self, code: str) -> bool:
        """Validate course code format: 2-4 uppercase letters + 3 digits.
        
        Examples: CS201, ENG301, MATH101
        """
        import re
        pattern = r'^[A-Z]{2,4}[0-9]{3}$'
        return bool(re.match(pattern, code))

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
