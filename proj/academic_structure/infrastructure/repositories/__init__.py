"""Repository package for academic_structure infrastructure."""

from .program_repository import ProgramRepository
from .stream_repository import StreamRepository
from .course_repository import CourseRepository

__all__ = ["ProgramRepository", "StreamRepository", "CourseRepository"]
