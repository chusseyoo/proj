from __future__ import annotations

from typing import Protocol


class AcademicStructurePort(Protocol):
    """Port to query academic-structure information required for validations."""

    def program_has_streams(self, program_id: int) -> bool:
        ...

    def stream_belongs_to_program(self, stream_id: int, program_id: int) -> bool:
        ...

    def course_belongs_to_program(self, course_id: int, program_id: int) -> bool:
        ...

    def get_course_lecturer(self, course_id: int) -> int:
        """Return lecturer_id assigned to course."""
        ...
