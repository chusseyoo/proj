"""Update Stream use case."""

from typing import Dict, Any

from ....domain.exceptions import (
    StreamNotFoundError,
    StreamAlreadyExistsError,
    ValidationError
)
from ....infrastructure.repositories import StreamRepository
from ...dto import StreamDTO, to_stream_dto


class UpdateStreamUseCase:
    """Use case for updating an existing stream."""

    def __init__(self, stream_repository: StreamRepository):
        """Initialize use case with repository dependency.
        
        Args:
            stream_repository: Repository for stream data access
        """
        self.stream_repository = stream_repository

    def execute(self, stream_id: int, updates: Dict[str, Any]) -> StreamDTO:
        """Update an existing stream.
        
        Args:
            stream_id: ID of the stream to update
            updates: Dictionary with fields to update:
                - stream_name (str, optional): New name (1-50 chars)
                - year_of_study (int, optional): New year (1-4)
                
        Returns:
            StreamDTO with updated stream data
            
        Raises:
            StreamNotFoundError: If stream does not exist
            ValidationError: If invalid data or trying to update program_id
            StreamAlreadyExistsError: If new name conflicts with existing stream
        """
        # Check if stream exists
        stream = self.stream_repository.get_by_id(stream_id)
        if stream is None:
            raise StreamNotFoundError(f"Stream with ID {stream_id} not found")
        
        # Prevent program_id updates
        if 'program_id' in updates:
            raise ValidationError(
                "program_id cannot be changed (move streams by deleting and recreating)"
            )
        
        # Validate updates
        allowed_fields = {'stream_name', 'year_of_study'}
        invalid_fields = set(updates.keys()) - allowed_fields
        if invalid_fields:
            raise ValidationError(
                f"Cannot update fields: {', '.join(invalid_fields)}"
            )
        
        # Validate stream_name if provided
        if 'stream_name' in updates:
            stream_name = updates['stream_name'].strip()
            if len(stream_name) < 1 or len(stream_name) > 50:
                raise ValidationError(
                    f"stream_name must be between 1 and 50 characters, got: {len(stream_name)}"
                )
            
            # Check for conflicts
            if stream_name != stream.stream_name:
                if self.stream_repository.exists_by_program_and_name(
                    stream.program_id, stream_name
                ):
                    raise StreamAlreadyExistsError(
                        f"Stream '{stream_name}' already exists for this program"
                    )
            
            updates['stream_name'] = stream_name
        
        # Validate year_of_study if provided
        if 'year_of_study' in updates:
            year_of_study = updates['year_of_study']
            if not isinstance(year_of_study, int) or year_of_study < 1 or year_of_study > 4:
                raise ValidationError(
                    f"year_of_study must be an integer between 1 and 4, got: {year_of_study}"
                )
        
        # Update via repository
        updated_stream = self.stream_repository.update(stream_id, updates)
        
        return to_stream_dto(updated_stream)
