"""Delete Course use case."""

from ....domain.exceptions import (
    CourseNotFoundError,
    CourseCannotBeDeletedError
)
from ....infrastructure.repositories import CourseRepository


class DeleteCourseUseCase:
    """Use case for deleting a course."""

    def __init__(self, course_repository: CourseRepository):
        """Initialize use case with repository dependency.
        
        Args:
            course_repository: Repository for course data access
        """
        self.course_repository = course_repository

    def execute(self, course_id: int) -> None:
        """Delete a course if no sessions are scheduled for it.
        
        Args:
            course_id: ID of the course to delete
            
        Raises:
            CourseNotFoundError: If course does not exist
            CourseCannotBeDeletedError: If course has scheduled sessions
        """
        # Retrieve course
        course = self.course_repository.get_by_id(course_id)
        if course is None:
            raise CourseNotFoundError(f"Course with ID {course_id} not found")
        
        # Check if course can be deleted (no sessions)
        if not self.course_repository.can_be_deleted(course_id):
            sessions_count = self.course_repository.count_sessions(course_id)
            raise CourseCannotBeDeletedError(
                f"Course '{course.course_name}' cannot be deleted: "
                f"has {sessions_count} scheduled session(s)"
            )
        
        # Safe to delete
        self.course_repository.delete(course_id)
