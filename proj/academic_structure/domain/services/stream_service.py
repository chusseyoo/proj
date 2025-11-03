"""Stream domain service implementing business rules for streams."""

from ..entities.stream import Stream
from ..entities.program import Program
from ..ports.stream_repository import StreamRepositoryPort
from ..ports.program_repository import ProgramRepositoryPort
from ..exceptions import (
    StreamNotFoundError,
    StreamAlreadyExistsError,
    StreamNotAllowedError,
    StreamCannotBeDeletedError,
    ProgramNotFoundError,
    ValidationError,
)


class StreamService:
    """Domain service for stream-level business rules and validation."""

    MIN_YEAR = 1
    MAX_YEAR = 4

    def __init__(
        self,
        stream_repo: StreamRepositoryPort,
        program_repo: ProgramRepositoryPort,
    ):
        self.stream_repo = stream_repo
        self.program_repo = program_repo

    def can_be_deleted(self, stream: Stream) -> bool:
        """Check if a stream can be safely deleted.
        
        A stream can be deleted if no students are assigned to it.
        """
        if stream.stream_id is None:
            return True

        students = self.stream_repo.students_count(stream.stream_id)
        return students == 0

    def validate_year_of_study(self, year: int) -> None:
        """Validate year of study is in valid range."""
        if not isinstance(year, int):
            raise ValidationError("Year of study must be an integer")
        
        if year < self.MIN_YEAR or year > self.MAX_YEAR:
            raise ValidationError(
                f"Year of study must be between {self.MIN_YEAR} and {self.MAX_YEAR}"
            )

    def validate_stream_name(self, name: str) -> None:
        """Validate stream name format."""
        if not name or not isinstance(name, str):
            raise ValidationError("Stream name must be a non-empty string")
        
        if len(name) < 1:
            raise ValidationError("Stream name must be at least 1 character")
        
        if len(name) > 50:
            raise ValidationError("Stream name must not exceed 50 characters")

    def validate_stream_for_creation(
        self, program_id: int, stream_name: str, year_of_study: int
    ) -> None:
        """Validate stream data before creation."""
        # Validate program exists and has streams enabled
        program = self.program_repo.get_by_id(program_id)
        if not program.has_streams:
            raise StreamNotAllowedError(
                f"Cannot create stream for program {program.program_code}: "
                "program does not have streams enabled"
            )
        
        # Validate year and name
        self.validate_year_of_study(year_of_study)
        self.validate_stream_name(stream_name)
        
        # Check uniqueness
        if self.stream_repo.exists_by_program_and_name(
            program_id, stream_name, year_of_study
        ):
            raise StreamAlreadyExistsError(
                f"Stream '{stream_name}' already exists for program {program_id} "
                f"year {year_of_study}"
            )

    def validate_stream_for_deletion(self, stream_id: int) -> None:
        """Validate stream can be deleted, raise exception if not."""
        stream = self.stream_repo.get_by_id(stream_id)
        if not self.can_be_deleted(stream):
            raise StreamCannotBeDeletedError(
                f"Cannot delete stream {stream.stream_name}: has assigned students"
            )
