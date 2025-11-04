"""Tests for DeleteStreamUseCase."""

import pytest
from unittest.mock import Mock

from academic_structure.domain.entities.stream import Stream
from academic_structure.domain.exceptions import (
    StreamNotFoundError,
    StreamCannotBeDeletedError
)
from academic_structure.application.use_cases.stream import DeleteStreamUseCase


class TestDeleteStreamUseCase:
    """Test cases for DeleteStreamUseCase."""

    @pytest.fixture
    def mock_stream_repository(self):
        """Create a mock StreamRepository."""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_stream_repository):
        """Create DeleteStreamUseCase with mocked repository."""
        return DeleteStreamUseCase(mock_stream_repository)

    @pytest.fixture
    def existing_stream(self):
        """Create an existing stream for delete tests."""
        return Stream(
            stream_id=1,
            stream_name='Stream to Delete',
            program_id=1,
            year_of_study=2
        )

    def test_delete_stream_successfully(self, use_case, mock_stream_repository, existing_stream):
        """Test deleting a stream successfully when no students assigned."""
        # Arrange
        mock_stream_repository.get_by_id.return_value = existing_stream
        mock_stream_repository.can_be_deleted.return_value = True

        # Act
        result = use_case.execute(stream_id=1)

        # Assert
        assert result is None
        mock_stream_repository.get_by_id.assert_called_once_with(1)
        mock_stream_repository.can_be_deleted.assert_called_once_with(1)
        mock_stream_repository.delete.assert_called_once_with(1)

    def test_delete_stream_not_found(self, use_case, mock_stream_repository):
        """Test deleting non-existent stream raises StreamNotFoundError."""
        # Arrange
        mock_stream_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(StreamNotFoundError) as exc_info:
            use_case.execute(stream_id=999)
        
        assert '999' in str(exc_info.value)
        mock_stream_repository.can_be_deleted.assert_not_called()
        mock_stream_repository.delete.assert_not_called()

    def test_delete_stream_with_assigned_students(self, use_case, mock_stream_repository, existing_stream):
        """Test that stream with assigned students cannot be deleted."""
        # Arrange
        mock_stream_repository.get_by_id.return_value = existing_stream
        mock_stream_repository.can_be_deleted.return_value = False
        mock_stream_repository.students_count.return_value = 5

        # Act & Assert
        with pytest.raises(StreamCannotBeDeletedError) as exc_info:
            use_case.execute(stream_id=1)
        
        error_message = str(exc_info.value)
        assert 'Stream to Delete' in error_message
        assert '5' in error_message
        assert 'student' in error_message.lower()
        
        mock_stream_repository.delete.assert_not_called()

    def test_delete_stream_checks_dependencies_before_deletion(self, use_case, mock_stream_repository, existing_stream):
        """Test that use case checks can_be_deleted before attempting deletion."""
        # Arrange
        mock_stream_repository.get_by_id.return_value = existing_stream
        mock_stream_repository.can_be_deleted.return_value = True

        # Act
        use_case.execute(stream_id=1)

        # Assert - verify order of operations
        assert mock_stream_repository.get_by_id.called
        assert mock_stream_repository.can_be_deleted.called
        assert mock_stream_repository.delete.called
        
        # Verify can_be_deleted is called before delete
        call_order = [call[0] for call in mock_stream_repository.method_calls]
        can_be_deleted_idx = call_order.index('can_be_deleted')
        delete_idx = call_order.index('delete')
        assert can_be_deleted_idx < delete_idx

    def test_delete_stream_different_ids(self, use_case, mock_stream_repository):
        """Test deleting streams with different IDs."""
        stream_ids = [1, 5, 100, 999]
        
        for sid in stream_ids:
            stream = Stream(
                stream_id=sid,
                stream_name=f'Stream {sid}',
                program_id=1,
                year_of_study=1
            )
            
            mock_stream_repository.get_by_id.return_value = stream
            mock_stream_repository.can_be_deleted.return_value = True
            
            use_case.execute(stream_id=sid)
            
            mock_stream_repository.get_by_id.assert_called_with(sid)
            mock_stream_repository.can_be_deleted.assert_called_with(sid)
            mock_stream_repository.delete.assert_called_with(sid)

    def test_delete_stream_with_many_students(self, use_case, mock_stream_repository, existing_stream):
        """Test error message with large number of students."""
        # Arrange
        mock_stream_repository.get_by_id.return_value = existing_stream
        mock_stream_repository.can_be_deleted.return_value = False
        mock_stream_repository.students_count.return_value = 150

        # Act & Assert
        with pytest.raises(StreamCannotBeDeletedError) as exc_info:
            use_case.execute(stream_id=1)
        
        error_message = str(exc_info.value)
        assert '150' in error_message
        mock_stream_repository.delete.assert_not_called()
