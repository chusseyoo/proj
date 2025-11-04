"""Course Data Transfer Object and mapper."""

from dataclasses import dataclass
from typing import Optional

from ...domain.entities.course import Course


@dataclass
class CourseDTO:
    """Data Transfer Object for Course entity.
    
    Used to transfer course data between application layer and API/UI.
    Optionally includes program_code and lecturer_name for enrichment.
    """
    course_id: Optional[int]
    course_code: str
    course_name: str
    program_id: int
    department_name: str
    lecturer_id: Optional[int]
    program_code: Optional[str] = None  # Optional enrichment from related Program
    lecturer_name: Optional[str] = None  # Optional enrichment from related Lecturer


def to_course_dto(
    course: Course,
    program_code: Optional[str] = None,
    lecturer_name: Optional[str] = None
) -> CourseDTO:
    """Convert Course domain entity to CourseDTO.
    
    Args:
        course: Course domain entity
        program_code: Optional program code for enrichment
        lecturer_name: Optional lecturer full name for enrichment
        
    Returns:
        CourseDTO with data from domain entity
    """
    return CourseDTO(
        course_id=course.course_id,
        course_code=course.course_code,
        course_name=course.course_name,
        program_id=course.program_id,
        department_name=course.department_name,
        lecturer_id=course.lecturer_id,
        program_code=program_code,
        lecturer_name=lecturer_name,
    )
