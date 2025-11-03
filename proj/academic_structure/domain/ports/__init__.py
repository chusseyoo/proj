"""Ports (protocols) for academic_structure domain."""

from .program_repository import ProgramRepositoryPort
from .stream_repository import StreamRepositoryPort
from .course_repository import CourseRepositoryPort

__all__ = ["ProgramRepositoryPort", "StreamRepositoryPort", "CourseRepositoryPort"]

