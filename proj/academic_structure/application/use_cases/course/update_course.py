"""Update Course use case."""

from typing import Dict, Any, Optional

from ....domain.exceptions import (
    CourseNotFoundError,
    CourseCodeAlreadyExistsError,
    LecturerNotFoundError,
    LecturerInactiveError,
    ValidationError
)
from ....infrastructure.repositories import CourseRepository
from ...dto import CourseDTO, to_course_dto


class UpdateCourseUseCase:
    """Use case for updating an existing course."""

    def __init__(self, course_repository: CourseRepository):
        """Initialize use case with repository dependency.
        
        Args:
            course_repository: Repository for course data access
        """
        self.course_repository = course_repository

    def execute(
        self,
        course_id: int,
        updates: Dict[str, Any],
        include_program_code: bool = False,
        include_lecturer_name: bool = False
    ) -> CourseDTO:
        """Update an existing course.
        
        Args:
            course_id: ID of the course to update
            updates: Dictionary with fields to update (mutable fields only):
                - course_name (str, optional): Updated name (3-200 chars)
                - department_name (str, optional): Updated department
                - lecturer_id (int or None, optional): Updated lecturer assignment
            include_program_code: Whether to include program_code in DTO
            include_lecturer_name: Whether to include lecturer_name in DTO
            
        Returns:
            CourseDTO with updated course data
            
        Raises:
            CourseNotFoundError: If course does not exist
            ValidationError: If updates are invalid or course_code change attempted
            LecturerNotFoundError: If lecturer_id provided but doesn't exist
            LecturerInactiveError: If lecturer account is not active
        """
        # Retrieve existing course
        course = self.course_repository.get_by_id(course_id)
        if course is None:
            raise CourseNotFoundError(f"Course with ID {course_id} not found")
        
        # Prevent course_code changes (immutable - students might reference it)
        if 'course_code' in updates:
            raise ValidationError(
                "course_code cannot be changed after creation (students may reference it)"
            )
        
        # Prevent program_id changes (immutable - structural relationship)
        if 'program_id' in updates:
            raise ValidationError(
                "program_id cannot be changed after creation (use delete and recreate)"
            )
        
        # Prepare updated fields (Course is frozen - must create new instance)
        updated_course_name = course.course_name
        updated_department_name = course.department_name
        updated_lecturer_id = course.lecturer_id
        
        # Validate and apply course_name update
        if 'course_name' in updates:
            course_name = updates['course_name'].strip()
            if len(course_name) < 3 or len(course_name) > 200:
                raise ValidationError(
                    f"course_name must be between 3 and 200 characters, got: {len(course_name)}"
                )
            updated_course_name = course_name
        
        # Validate and apply department_name update
        if 'department_name' in updates:
            department_name = updates['department_name'].strip()
            if len(department_name) < 3 or len(department_name) > 150:
                raise ValidationError(
                    f"department_name must be between 3 and 150 characters, got: {len(department_name)}"
                )
            updated_department_name = department_name
        
        # Validate and apply lecturer_id update (cross-context)
        if 'lecturer_id' in updates:
            lecturer_id = updates['lecturer_id']
            
            # Allow setting to None (unassign lecturer)
            if lecturer_id is not None:
                self._validate_lecturer(lecturer_id)
            
            updated_lecturer_id = lecturer_id
        
        # Create new immutable course instance with updates
        from ....domain.entities.course import Course
        modified_course = Course(
            course_id=course.course_id,
            course_name=updated_course_name,
            course_code=course.course_code,
            program_id=course.program_id,
            department_name=updated_department_name,
            lecturer_id=updated_lecturer_id
        )
        
        # Save updated course
        updated_course = self.course_repository.update(modified_course)
        
        # Optional enrichment
        program_code = None
        lecturer_name = None
        
        if include_program_code:
            # Import here to avoid circular dependency
            from ....infrastructure.repositories import ProgramRepository
            program_repository = ProgramRepository()
            program = program_repository.get_by_id(updated_course.program_id)
            if program:
                program_code = program.program_code
        
        if include_lecturer_name and updated_course.lecturer_id:
            lecturer_name = self._get_lecturer_name(updated_course.lecturer_id)
        
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
