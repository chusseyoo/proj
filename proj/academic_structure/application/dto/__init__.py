"""Data Transfer Objects package for academic_structure application layer.

This package contains DTOs used to transfer data between the application layer
and external interfaces (API, UI). DTOs provide a stable contract and allow
enrichment with related data (e.g., program_code, lecturer_name).
"""

from .program_dto import ProgramDTO, to_program_dto
from .stream_dto import StreamDTO, to_stream_dto
from .course_dto import CourseDTO, to_course_dto

__all__ = [
    # DTOs
    "ProgramDTO",
    "StreamDTO",
    "CourseDTO",
    # Mappers
    "to_program_dto",
    "to_stream_dto",
    "to_course_dto",
]
