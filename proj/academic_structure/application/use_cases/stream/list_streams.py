"""List Streams use case."""

from typing import List, Optional

from ....domain.exceptions import ProgramNotFoundError
from ....infrastructure.repositories import StreamRepository, ProgramRepository
from ...dto import StreamDTO, to_stream_dto


class ListStreamsByProgramUseCase:
    """Use case for listing streams by program."""

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

    def execute(
        self,
        program_id: int,
        year_of_study: Optional[int] = None,
        include_program_code: bool = False
    ) -> List[StreamDTO]:
        """List streams by program, optionally filtered by year.
        
        Args:
            program_id: ID of the program
            year_of_study: Optional filter by year (1-4)
            include_program_code: Whether to enrich with program_code
            
        Returns:
            List of StreamDTOs
            
        Raises:
            ProgramNotFoundError: If program with given ID does not exist
        """
        # Validate that the program exists
        program = self.program_repository.find_by_id(program_id)
        if program is None:
            raise ProgramNotFoundError(f"Program with ID {program_id} not found")
        
        if year_of_study is not None:
            streams = self.stream_repository.list_by_program_and_year(
                program_id, year_of_study
            )
        else:
            streams = self.stream_repository.list_by_program(program_id)
        
        # Optional enrichment with program_code
        program_code = None
        if include_program_code and program:
            program_code = program.program_code
        
        return [to_stream_dto(stream, program_code=program_code) for stream in streams]
