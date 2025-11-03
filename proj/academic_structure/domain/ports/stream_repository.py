"""Stream repository port for academic_structure domain."""

from typing import Protocol, Optional, Iterable

from ..entities.stream import Stream


class StreamRepositoryPort(Protocol):
    """Repository port for Stream persistence operations."""

    def get_by_id(self, stream_id: int) -> Stream:
        """Get stream by ID. Raises if not found."""
        ...

    def find_by_id(self, stream_id: int) -> Optional[Stream]:
        """Get stream by ID, return None if not found."""
        ...

    def list_by_program(self, program_id: int) -> Iterable[Stream]:
        """Get all streams for a program, ordered by year and name."""
        ...

    def list_by_program_and_year(self, program_id: int, year_of_study: int) -> Iterable[Stream]:
        """Get streams for specific program and year."""
        ...

    def exists_by_program_and_name(
        self, program_id: int, stream_name: str, year_of_study: int
    ) -> bool:
        """Check if stream already exists (unique_together constraint)."""
        ...

    def create(self, data: dict) -> Stream:
        """Create new stream."""
        ...

    def update(self, stream_id: int, data: dict) -> Stream:
        """Update stream fields."""
        ...

    def delete(self, stream_id: int) -> None:
        """Delete stream."""
        ...

    def can_be_deleted(self, stream_id: int) -> bool:
        """Check if stream can be safely deleted (no students assigned)."""
        ...

    def students_count(self, stream_id: int) -> int:
        """Count students assigned to this stream."""
        ...
