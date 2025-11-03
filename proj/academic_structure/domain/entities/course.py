from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Course:
    """Domain entity representing a course.
    
    Immutable entity. Lecturer assignment is optional initially
    but required before sessions can be created.
    """

    course_id: Optional[int]
    course_name: str
    course_code: str
    program_id: int
    department_name: str
    lecturer_id: Optional[int] = None

    def __str__(self) -> str:
        return f"{self.course_code} - {self.course_name}"

    def is_assigned_to_lecturer(self) -> bool:
        """Check if course has an assigned lecturer."""
        return self.lecturer_id is not None
