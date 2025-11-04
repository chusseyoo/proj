"""Get Stream use case."""

from typing import Optional

from ....domain.exceptions import StreamNotFoundError
from ....infrastructure.repositories import StreamRepository, ProgramRepository
from ...dto import StreamDTO, to_stream_dto


class GetStreamUseCase:
    """Use case for retrieving a single stream by ID."""

    def __init__(
        self,
        stream_repository: StreamRepository,
        program_repository: ProgramRepository
    ):
        """Initialize use case with repository dependencies.
        
        Args:
            stream_repository: Repository for stream data access
            program_repository: Repository for program data access (for enrichment)
        """
        self.stream_repository = stream_repository
        self.program_repository = program_repository

    def execute(self, stream_id: int, include_program_code: bool = False) -> StreamDTO:
        """Get stream by ID.
        
        Args:
            stream_id: ID of the stream to retrieve
            include_program_code: Whether to enrich with program_code
            
        Returns:
            StreamDTO with stream data
            
        Raises:
            StreamNotFoundError: If stream with given ID does not exist
        """
        stream = self.stream_repository.get_by_id(stream_id)
        
        if stream is None:
            raise StreamNotFoundError(f"Stream with ID {stream_id} not found")
        
        # Optional enrichment with program_code
        program_code = None
        if include_program_code:
            program = self.program_repository.get_by_id(stream.program_id)
            if program:
                program_code = program.program_code
        
        return to_stream_dto(stream, program_code=program_code)
