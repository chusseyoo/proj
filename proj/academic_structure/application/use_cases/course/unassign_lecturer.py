"""Unassign Lecturer from Course use case."""

from typing import Optional

from ....domain.exceptions import CourseNotFoundError
from ....infrastructure.repositories import CourseRepository
from ...dto import CourseDTO, to_course_dto


class UnassignLecturerUseCase:
    """Use case for unassigning a lecturer from a course."""

    def __init__(self, course_repository: CourseRepository):
        """Initialize use case with repository dependency.
        
        Args:
            course_repository: Repository for course data access
        """
        self.course_repository = course_repository

    def execute(
        self,
        course_id: int,
        include_program_code: bool = False
    ) -> CourseDTO:
        """Unassign the lecturer from a course.
        
        Args:
            course_id: ID of the course
            include_program_code: Whether to include program_code in DTO
            
        Returns:
            CourseDTO with updated course data (lecturer_id=None, lecturer_name=None)
            
        Raises:
            CourseNotFoundError: If course does not exist
        """
        # Retrieve course
        course = self.course_repository.get_by_id(course_id)
        if course is None:
            raise CourseNotFoundError(f"Course with ID {course_id} not found")
        
        # Unassign lecturer (create new instance - Course is frozen)
        from ....domain.entities.course import Course
        unassigned_course = Course(
            course_id=course.course_id,
            course_name=course.course_name,
            course_code=course.course_code,
            program_id=course.program_id,
            department_name=course.department_name,
            lecturer_id=None
        )
        updated_course = self.course_repository.update(unassigned_course)
        
        # Enrichment
        program_code = None
        if include_program_code:
            from ....infrastructure.repositories import ProgramRepository
            program_repository = ProgramRepository()
            program = program_repository.get_by_id(updated_course.program_id)
            if program:
                program_code = program.program_code
        
        return to_course_dto(
            updated_course,
            program_code=program_code,
            lecturer_name=None  # Always None after unassignment
        )
