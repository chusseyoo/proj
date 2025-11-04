"""List Courses use case."""

from typing import List, Optional

from ....infrastructure.repositories import CourseRepository, ProgramRepository
from ...dto import CourseDTO, to_course_dto


class ListCoursesUseCase:
    """Use case for listing courses with optional filtering."""

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
        program_id: Optional[int] = None,
        lecturer_id: Optional[int] = None,
        include_program_code: bool = False,
        include_lecturer_name: bool = False
    ) -> List[CourseDTO]:
        """List courses with optional filters.
        
        Args:
            program_id: Optional filter by program
            lecturer_id: Optional filter by lecturer
            include_program_code: Whether to enrich with program_code
            include_lecturer_name: Whether to enrich with lecturer_name
            
        Returns:
            List of CourseDTOs
        """
        # Apply filters
        if program_id and lecturer_id:
            # Both filters - need to combine
            all_courses = self.course_repository.list_by_program(program_id)
            courses = [c for c in all_courses if c.lecturer_id == lecturer_id]
        elif program_id:
            courses = self.course_repository.list_by_program(program_id)
        elif lecturer_id:
            courses = self.course_repository.list_by_lecturer(lecturer_id)
        else:
            # No filters - get all (might want to implement list_all in repository)
            courses = self.course_repository.list_by_program(program_id=None)
        
        # Build enrichment maps if needed
        program_codes = {}
        lecturer_names = {}
        
        if include_program_code:
            unique_program_ids = set(c.program_id for c in courses)
            for pid in unique_program_ids:
                program = self.program_repository.get_by_id(pid)
                if program:
                    program_codes[pid] = program.program_code
        
        if include_lecturer_name:
            from user_management.infrastructure.orm.django_models import LecturerProfile
            unique_lecturer_ids = set(
                c.lecturer_id for c in courses if c.lecturer_id is not None
            )
            for lid in unique_lecturer_ids:
                try:
                    lecturer_profile = LecturerProfile.objects.select_related('user').get(
                        lecturer_id=lid
                    )
                    lecturer_names[lid] = lecturer_profile.user.get_full_name()
                except LecturerProfile.DoesNotExist:
                    lecturer_names[lid] = None
        
        # Convert to DTOs with enrichment
        return [
            to_course_dto(
                course,
                program_code=program_codes.get(course.program_id),
                lecturer_name=lecturer_names.get(course.lecturer_id)
            )
            for course in courses
        ]


class ListUnassignedCoursesUseCase:
    """Use case for listing courses without assigned lecturers."""

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

    def execute(self, include_program_code: bool = False) -> List[CourseDTO]:
        """List courses without assigned lecturers.
        
        Args:
            include_program_code: Whether to enrich with program_code
            
        Returns:
            List of CourseDTOs for unassigned courses
        """
        courses = self.course_repository.list_unassigned()
        
        # Optional enrichment with program codes
        program_codes = {}
        if include_program_code:
            unique_program_ids = set(c.program_id for c in courses)
            for pid in unique_program_ids:
                program = self.program_repository.get_by_id(pid)
                if program:
                    program_codes[pid] = program.program_code
        
        return [
            to_course_dto(course, program_code=program_codes.get(course.program_id))
            for course in courses
        ]
