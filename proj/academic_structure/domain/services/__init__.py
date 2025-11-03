"""Services for academic_structure domain."""

from .program_service import ProgramService
from .stream_service import StreamService
from .course_service import CourseService

__all__ = ["ProgramService", "StreamService", "CourseService"]
