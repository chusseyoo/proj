"""Course repository port for academic_structure domain."""

from typing import Protocol, Optional, Iterable

from ..entities.course import Course


class CourseRepositoryPort(Protocol):
    """Repository port for Course persistence operations."""

    def get_by_id(self, course_id: int) -> Course:
        """Get course by ID. Raises if not found."""
        ...

    def find_by_id(self, course_id: int) -> Optional[Course]:
        """Get course by ID, return None if not found."""
        ...

    def get_by_code(self, course_code: str) -> Course:
        """Get course by code (case-insensitive). Raises if not found."""
        ...

    def exists_by_code(self, course_code: str) -> bool:
        """Check if course code already exists."""
        ...

    def list_by_program(self, program_id: int) -> Iterable[Course]:
        """Get all courses for a program."""
        ...

    def list_by_lecturer(self, lecturer_id: int) -> Iterable[Course]:
        """Get all courses assigned to a lecturer."""
        ...

    def list_unassigned(self) -> Iterable[Course]:
        """Get all courses with no assigned lecturer."""
        ...

    def create(self, data: dict) -> Course:
        """Create new course."""
        ...

    def update(self, course_id: int, data: dict) -> Course:
        """Update course fields."""
        ...

    def assign_lecturer(self, course_id: int, lecturer_id: int) -> Course:
        """Assign lecturer to course."""
        ...

    def unassign_lecturer(self, course_id: int) -> Course:
        """Remove lecturer from course (set to NULL)."""
        ...

    def delete(self, course_id: int) -> None:
        """Delete course."""
        ...

    def can_be_deleted(self, course_id: int) -> bool:
        """Check if course can be safely deleted (no sessions exist)."""
        ...

    def sessions_count(self, course_id: int) -> int:
        """Count sessions for this course."""
        ...
