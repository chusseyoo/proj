"""Course domain service implementing business rules for courses."""

from ..entities.course import Course
from ..ports.course_repository import CourseRepositoryPort
from ..ports.program_repository import ProgramRepositoryPort
from ..exceptions import (
    CourseNotFoundError,
    CourseCodeAlreadyExistsError,
    CourseCannotBeDeletedError,
    ProgramNotFoundError,
    LecturerNotFoundError,
    LecturerInactiveError,
    ValidationError,
)


class CourseService:
    """Domain service for course-level business rules and validation."""

    def __init__(
        self,
        course_repo: CourseRepositoryPort,
        program_repo: ProgramRepositoryPort,
    ):
        self.course_repo = course_repo
        self.program_repo = program_repo

    def can_be_deleted(self, course: Course) -> bool:
        """Check if a course can be safely deleted.
        
        A course can be deleted if no sessions exist for it.
        """
        if course.course_id is None:
            return True

        sessions = self.course_repo.sessions_count(course.course_id)
        return sessions == 0

    def validate_course_code(self, code: str) -> str:
        """Validate and normalize course code.
        
        Returns uppercase code if valid, raises ValidationError otherwise.
        Recommended pattern: 2-6 uppercase letters + 2-4 digits (e.g., CS201, ENG301).
        """
        if not code or not isinstance(code, str):
            raise ValidationError("Course code must be a non-empty string")
        
        normalized = code.strip().upper()
        
        # Basic validation: should have letters and digits
        if len(normalized) < 4 or len(normalized) > 10:
            raise ValidationError("Course code must be 4-10 characters")
        
        # Check it has both letters and digits
        has_letter = any(c.isalpha() for c in normalized)
        has_digit = any(c.isdigit() for c in normalized)
        
        if not (has_letter and has_digit):
            raise ValidationError(
                "Course code must contain both letters and digits (e.g., CS201)"
            )
        
        return normalized

    def validate_course_name(self, name: str) -> None:
        """Validate course name format."""
        if not name or not isinstance(name, str):
            raise ValidationError("Course name must be a non-empty string")
        
        if len(name) < 3:
            raise ValidationError("Course name must be at least 3 characters")
        
        if len(name) > 150:
            raise ValidationError("Course name must not exceed 150 characters")

    def validate_course_for_creation(self, data: dict) -> None:
        """Validate course data before creation."""
        # Validate code format
        code = data.get("course_code", "")
        normalized_code = self.validate_course_code(code)
        
        # Check uniqueness
        if self.course_repo.exists_by_code(normalized_code):
            raise CourseCodeAlreadyExistsError(
                f"Course code '{normalized_code}' already exists"
            )
        
        # Validate name
        name = data.get("course_name", "")
        self.validate_course_name(name)
        
        # Validate program exists
        program_id = data.get("program_id")
        if program_id is None:
            raise ValidationError("program_id is required")
        
        if not self.program_repo.exists_by_id(program_id):
            raise ProgramNotFoundError(f"Program {program_id} not found")
        
        # Validate department
        dept = data.get("department_name", "")
        if not dept or len(dept) < 3:
            raise ValidationError("Department name must be at least 3 characters")

    def validate_lecturer_assignment(self, lecturer_id: int) -> None:
        """Validate lecturer can be assigned.
        
        Note: This requires cross-context validation with User Management.
        In practice, this should call User Management service to check:
        - Lecturer exists
        - Lecturer's user is active
        
        For now, we define the interface; implementation will be in application layer.
        """
        # Cross-context validation placeholder
        # Application layer should inject User Management service and perform actual checks
        if lecturer_id is None:
            raise ValidationError("lecturer_id cannot be None")

    def validate_course_for_deletion(self, course_id: int) -> None:
        """Validate course can be deleted, raise exception if not."""
        course = self.course_repo.get_by_id(course_id)
        if not self.can_be_deleted(course):
            raise CourseCannotBeDeletedError(
                f"Cannot delete course {course.course_code}: has existing sessions"
            )
