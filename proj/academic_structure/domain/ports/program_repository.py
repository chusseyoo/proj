"""Program repository port for academic_structure domain."""

from typing import Protocol, Optional, Iterable

from ..entities.program import Program


class ProgramRepositoryPort(Protocol):
    """Repository port for Program persistence operations."""

    def get_by_id(self, program_id: int) -> Program:
        """Get program by ID. Raises if not found."""
        ...

    def find_by_id(self, program_id: int) -> Optional[Program]:
        """Get program by ID, return None if not found."""
        ...

    def get_by_code(self, program_code: str) -> Program:
        """Get program by code (case-insensitive). Raises if not found."""
        ...

    def exists_by_code(self, program_code: str) -> bool:
        """Check if program code already exists."""
        ...

    def exists_by_id(self, program_id: int) -> bool:
        """Check if program exists by ID."""
        ...

    def list_all(self) -> Iterable[Program]:
        """Get all programs ordered by name."""
        ...

    def list_by_department(self, department_name: str) -> Iterable[Program]:
        """Get all programs in a department."""
        ...

    def list_with_streams(self) -> Iterable[Program]:
        """Get programs that have streams enabled."""
        ...

    def list_without_streams(self) -> Iterable[Program]:
        """Get programs without streams."""
        ...

    def create(self, data: dict) -> Program:
        """Create new program."""
        ...

    def update(self, program_id: int, data: dict) -> Program:
        """Update program fields."""
        ...

    def delete(self, program_id: int) -> None:
        """Delete program (cascades to streams and courses)."""
        ...

    def can_be_deleted(self, program_id: int) -> bool:
        """Check if program can be safely deleted (no students or courses)."""
        ...

    def students_count(self, program_id: int) -> int:
        """Count students enrolled in this program."""
        ...

    def courses_count(self, program_id: int) -> int:
        """Count courses in this program."""
        ...
