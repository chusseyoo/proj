"""Get Course use case."""

from typing import Optional

from ....domain.exceptions import CourseNotFoundError
from ....infrastructure.repositories import CourseRepository, ProgramRepository
from ...dto import CourseDTO, to_course_dto


class GetCourseUseCase:
    """Use case for retrieving a single course by ID."""

    def __init__(
        self,
        course_repository: CourseRepository,
        program_repository: ProgramRepository
    ):
        """Initialize use case with repository dependencies.
        
        Args:
            course_repository: Repository for course data access
            program_repository: Repository for program data access (for enrichment)
        """
        self.course_repository = course_repository
        self.program_repository = program_repository

    def execute(
        self,
        course_id: int,
        include_program_code: bool = False,
        include_lecturer_name: bool = False
    ) -> CourseDTO:
        """Get course by ID.
        
        Args:
            course_id: ID of the course to retrieve
            include_program_code: Whether to enrich with program_code
            include_lecturer_name: Whether to enrich with lecturer_name
            
        Returns:
            CourseDTO with course data
            
        Raises:
            CourseNotFoundError: If course with given ID does not exist
        """
        course = self.course_repository.find_by_id(course_id)
        
        if course is None:
            raise CourseNotFoundError(f"Course with ID {course_id} not found")
        
        # Optional enrichment
        program_code = None
        lecturer_name = None
        
        if include_program_code:
            program = self.program_repository.get_by_id(course.program_id)
            if program:
                program_code = program.program_code
        
        if include_lecturer_name and course.lecturer_id:
            # Cross-context: Get lecturer name from user_management
            from user_management.infrastructure.orm.django_models import LecturerProfile
            try:
                lecturer_profile = LecturerProfile.objects.select_related('user').get(
                    lecturer_id=course.lecturer_id
                )
                lecturer_name = lecturer_profile.user.get_full_name()
            except LecturerProfile.DoesNotExist:
                lecturer_name = None
        
        return to_course_dto(
            course,
            program_code=program_code,
            lecturer_name=lecturer_name
        )


class GetCourseByCodeUseCase:
    """Use case for retrieving a single course by code."""

    def __init__(
        self,
        course_repository: CourseRepository,
        program_repository: ProgramRepository
    ):
        """Initialize use case with repository dependencies.
        
        Args:
            course_repository: Repository for course data access
            program_repository: Repository for program data access (for enrichment)
        """
        self.course_repository = course_repository
        self.program_repository = program_repository

    def execute(
        self,
        course_code: str,
        include_program_code: bool = False,
        include_lecturer_name: bool = False
    ) -> CourseDTO:
        """Get course by code (case-insensitive).
        
        Args:
            course_code: Code of the course to retrieve
            include_program_code: Whether to enrich with program_code
            include_lecturer_name: Whether to enrich with lecturer_name
            
        Returns:
            CourseDTO with course data
            
        Raises:
            CourseNotFoundError: If course with given code does not exist
        """
        course = self.course_repository.get_by_code(course_code)
        
        if course is None:
            raise CourseNotFoundError(f"Course with code '{course_code}' not found")
        
        # Optional enrichment
        program_code = None
        lecturer_name = None
        
        if include_program_code:
            program = self.program_repository.get_by_id(course.program_id)
            if program:
                program_code = program.program_code
        
        if include_lecturer_name and course.lecturer_id:
            # Cross-context: Get lecturer name from user_management
            from user_management.infrastructure.orm.django_models import LecturerProfile
            try:
                lecturer_profile = LecturerProfile.objects.select_related('user').get(
                    lecturer_id=course.lecturer_id
                )
                lecturer_name = lecturer_profile.user.get_full_name()
            except LecturerProfile.DoesNotExist:
                lecturer_name = None
        
        return to_course_dto(
            course,
            program_code=program_code,
            lecturer_name=lecturer_name
        )
