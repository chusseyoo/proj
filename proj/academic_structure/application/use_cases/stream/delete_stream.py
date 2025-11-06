"""Delete Stream use case."""

from ....domain.exceptions import StreamNotFoundError, StreamCannotBeDeletedError
from ....infrastructure.repositories import StreamRepository


class DeleteStreamUseCase:
    """Use case for safely deleting a stream."""

    def __init__(self, stream_repository: StreamRepository):
        """Initialize use case with repository dependency.
        
        Args:
            stream_repository: Repository for stream data access
        """
        self.stream_repository = stream_repository

    def execute(self, stream_id: int) -> None:
        """Delete a stream if it has no dependencies.
        
        A stream can only be deleted if it has no students assigned to it.
        
        Args:
            stream_id: ID of the stream to delete
            
        Raises:
            StreamNotFoundError: If stream does not exist
            StreamCannotBeDeletedError: If stream has assigned students
        """
        # Check if stream exists
        stream = self.stream_repository.find_by_id(stream_id)
        if stream is None:
            raise StreamNotFoundError(f"Stream with ID {stream_id} not found")
        
        # Check if stream can be deleted (no students)
        if not self.stream_repository.can_be_deleted(stream_id):
            students_count = self.stream_repository.students_count(stream_id)
            raise StreamCannotBeDeletedError(
                f"Cannot delete stream '{stream.stream_name}': "
                f"has {students_count} assigned student(s)"
            )
        
        # Delete stream
        self.stream_repository.delete(stream_id)
