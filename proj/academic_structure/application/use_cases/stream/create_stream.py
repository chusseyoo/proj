"""Create Stream use case."""

from typing import Dict, Any

from ....domain.exceptions import (
    ProgramNotFoundError,
    StreamNotAllowedError,
    StreamAlreadyExistsError,
    ValidationError
)
from ....infrastructure.repositories import StreamRepository, ProgramRepository
from ...dto import StreamDTO, to_stream_dto


class CreateStreamUseCase:
    """Use case for creating a new stream."""

    def __init__(
        self,
        stream_repository: StreamRepository,
        program_repository: ProgramRepository
    ):
        """Initialize use case with repository dependencies.
        
        Args:
            stream_repository: Repository for stream data access
            program_repository: Repository for program data access
        """
        self.stream_repository = stream_repository
        self.program_repository = program_repository

    def execute(self, data: Dict[str, Any]) -> StreamDTO:
        """Create a new stream.
        
        Args:
            data: Dictionary with stream data:
                - program_id (int): Parent program ID
                - stream_name (str): Name of the stream (1-50 chars)
                - year_of_study (int): Year level (1-4)
                
        Returns:
            StreamDTO with created stream data
            
        Raises:
            ValidationError: If input data is invalid
            ProgramNotFoundError: If program does not exist
            StreamNotAllowedError: If program has has_streams=False
            StreamAlreadyExistsError: If stream name already exists for program/year
        """
        # Validate required fields
        required_fields = ['program_id', 'stream_name', 'year_of_study']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Extract and validate data
        program_id = data['program_id']
        stream_name = data['stream_name'].strip()
        year_of_study = data['year_of_study']
        
        # Validate stream_name length
        if len(stream_name) < 1 or len(stream_name) > 50:
            raise ValidationError(
                f"stream_name must be between 1 and 50 characters, got: {len(stream_name)}"
            )
        
        # Validate year_of_study range
        if not isinstance(year_of_study, int) or year_of_study < 1 or year_of_study > 4:
            raise ValidationError(
                f"year_of_study must be an integer between 1 and 4, got: {year_of_study}"
            )
        
        # Check if program exists
        program = self.program_repository.find_by_id(program_id)
        if program is None:
            raise ProgramNotFoundError(f"Program with ID {program_id} not found")
        
        # Check if program allows streams
        if not program.has_streams:
            raise StreamNotAllowedError(
                f"Program '{program.program_code}' does not allow streams (has_streams=False)"
            )
        
        # Check if stream already exists for this program/year/name
        if self.stream_repository.exists_by_program_and_name(program_id, stream_name, year_of_study):
            raise StreamAlreadyExistsError(
                f"Stream '{stream_name}' already exists for program '{program.program_code}' in year {year_of_study}"
            )
        
        # Create stream via repository
        stream_data = {
            'program_id': program_id,
            'stream_name': stream_name,
            'year_of_study': year_of_study,
        }
        
        stream = self.stream_repository.create(stream_data)
        
        return to_stream_dto(stream, program_code=program.program_code)
