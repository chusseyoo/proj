"""Tests for UpdateStreamUseCase."""

import pytest
from unittest.mock import Mock

from academic_structure.domain.entities.stream import Stream
from academic_structure.domain.exceptions import (
    StreamNotFoundError,
    StreamAlreadyExistsError,
    ValidationError
)
from academic_structure.application.use_cases.stream import UpdateStreamUseCase
from academic_structure.application.dto import StreamDTO


class TestUpdateStreamUseCase:
    """Test cases for UpdateStreamUseCase."""

    @pytest.fixture
    def mock_stream_repository(self):
        """Create a mock StreamRepository."""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_stream_repository):
        """Create UpdateStreamUseCase with mocked repository."""
        return UpdateStreamUseCase(mock_stream_repository)

    @pytest.fixture
    def existing_stream(self):
        """Create an existing stream for update tests."""
        return Stream(
            stream_id=1,
            stream_name='Original Stream',
            program_id=1,
            year_of_study=2
        )

    def test_update_stream_name(self, use_case, mock_stream_repository, existing_stream):
        """Test updating stream_name successfully."""
        # Arrange
        updates = {'stream_name': 'Updated Stream Name'}
        
        updated_stream = Stream(
            stream_id=1,
            stream_name='Updated Stream Name',
            program_id=1,
            year_of_study=2
        )
        
        mock_stream_repository.get_by_id.return_value = existing_stream
        mock_stream_repository.exists_by_program_and_name.return_value = False
        mock_stream_repository.update.return_value = updated_stream

        # Act
        result = use_case.execute(stream_id=1, updates=updates)

        # Assert
        assert isinstance(result, StreamDTO)
        assert result.stream_name == 'Updated Stream Name'
        assert result.year_of_study == 2  # Unchanged
        
        mock_stream_repository.get_by_id.assert_called_once_with(1)
        mock_stream_repository.update.assert_called_once()

    def test_update_year_of_study(self, use_case, mock_stream_repository, existing_stream):
        """Test updating year_of_study successfully."""
        # Arrange
        updates = {'year_of_study': 3}
        
        updated_stream = Stream(
            stream_id=1,
            stream_name='Original Stream',
            program_id=1,
            year_of_study=3
        )
        
        mock_stream_repository.get_by_id.return_value = existing_stream
        mock_stream_repository.update.return_value = updated_stream

        # Act
        result = use_case.execute(stream_id=1, updates=updates)

        # Assert
        assert result.year_of_study == 3
        assert result.stream_name == 'Original Stream'  # Unchanged

    def test_update_multiple_fields(self, use_case, mock_stream_repository, existing_stream):
        """Test updating multiple fields at once."""
        # Arrange
        updates = {
            'stream_name': 'New Stream Name',
            'year_of_study': 4
        }
        
        updated_stream = Stream(
            stream_id=1,
            stream_name='New Stream Name',
            program_id=1,
            year_of_study=4
        )
        
        mock_stream_repository.get_by_id.return_value = existing_stream
        mock_stream_repository.exists_by_program_and_name.return_value = False
        mock_stream_repository.update.return_value = updated_stream

        # Act
        result = use_case.execute(stream_id=1, updates=updates)

        # Assert
        assert result.stream_name == 'New Stream Name'
        assert result.year_of_study == 4

    def test_update_stream_not_found(self, use_case, mock_stream_repository):
        """Test updating non-existent stream raises StreamNotFoundError."""
        # Arrange
        mock_stream_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(StreamNotFoundError) as exc_info:
            use_case.execute(stream_id=999, updates={'stream_name': 'Test'})
        
        assert '999' in str(exc_info.value)
        mock_stream_repository.update.assert_not_called()

    def test_update_program_id_raises_error(self, use_case, mock_stream_repository, existing_stream):
        """Test that attempting to change program_id raises ValidationError."""
        # Arrange
        updates = {'program_id': 2}
        
        mock_stream_repository.get_by_id.return_value = existing_stream

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(stream_id=1, updates=updates)
        
        assert 'program_id' in str(exc_info.value).lower()
        assert 'cannot be changed' in str(exc_info.value).lower()
        mock_stream_repository.update.assert_not_called()

    def test_update_stream_with_short_name(self, use_case, mock_stream_repository, existing_stream):
        """Test that stream_name less than 1 character raises ValidationError."""
        # Arrange
        updates = {'stream_name': ''}  # Empty string
        
        mock_stream_repository.get_by_id.return_value = existing_stream

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(stream_id=1, updates=updates)
        
        assert 'stream_name' in str(exc_info.value).lower()
        mock_stream_repository.update.assert_not_called()

    def test_update_stream_with_long_name(self, use_case, mock_stream_repository, existing_stream):
        """Test that stream_name longer than 50 characters raises ValidationError."""
        # Arrange
        updates = {'stream_name': 'A' * 51}
        
        mock_stream_repository.get_by_id.return_value = existing_stream

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(stream_id=1, updates=updates)
        
        assert 'stream_name' in str(exc_info.value).lower()
        assert '50' in str(exc_info.value)
        mock_stream_repository.update.assert_not_called()

    def test_update_stream_with_invalid_year_below_range(self, use_case, mock_stream_repository, existing_stream):
        """Test that year_of_study < 1 raises ValidationError."""
        # Arrange
        updates = {'year_of_study': 0}
        
        mock_stream_repository.get_by_id.return_value = existing_stream

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(stream_id=1, updates=updates)
        
        assert 'year_of_study' in str(exc_info.value).lower()
        mock_stream_repository.update.assert_not_called()

    def test_update_stream_with_invalid_year_above_range(self, use_case, mock_stream_repository, existing_stream):
        """Test that year_of_study > 4 raises ValidationError."""
        # Arrange
        updates = {'year_of_study': 5}
        
        mock_stream_repository.get_by_id.return_value = existing_stream

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(stream_id=1, updates=updates)
        
        assert 'year_of_study' in str(exc_info.value).lower()
        mock_stream_repository.update.assert_not_called()

    def test_update_stream_with_duplicate_name(self, use_case, mock_stream_repository, existing_stream):
        """Test that updating to duplicate stream name raises StreamAlreadyExistsError."""
        # Arrange
        updates = {'stream_name': 'Existing Stream'}
        
        mock_stream_repository.get_by_id.return_value = existing_stream
        mock_stream_repository.exists_by_program_and_name.return_value = True

        # Act & Assert
        with pytest.raises(StreamAlreadyExistsError) as exc_info:
            use_case.execute(stream_id=1, updates=updates)
        
        assert 'Existing Stream' in str(exc_info.value)
        mock_stream_repository.update.assert_not_called()

    def test_update_stream_trims_whitespace(self, use_case, mock_stream_repository, existing_stream):
        """Test that whitespace is trimmed from updated stream_name."""
        # Arrange
        updates = {'stream_name': '  Trimmed Stream  '}
        
        updated_stream = Stream(
            stream_id=1,
            stream_name='Trimmed Stream',
            program_id=1,
            year_of_study=2
        )
        
        mock_stream_repository.get_by_id.return_value = existing_stream
        mock_stream_repository.exists_by_program_and_name.return_value = False
        mock_stream_repository.update.return_value = updated_stream

        # Act
        result = use_case.execute(stream_id=1, updates=updates)

        # Assert
        assert result.stream_name == 'Trimmed Stream'

    def test_update_stream_with_empty_updates(self, use_case, mock_stream_repository, existing_stream):
        """Test updating stream with empty updates dictionary."""
        # Arrange
        updates = {}
        
        mock_stream_repository.get_by_id.return_value = existing_stream
        mock_stream_repository.update.return_value = existing_stream

        # Act
        result = use_case.execute(stream_id=1, updates=updates)

        # Assert
        assert result.stream_id == 1
        assert result.stream_name == existing_stream.stream_name
        mock_stream_repository.update.assert_called_once()

    def test_update_stream_name_to_same_value(self, use_case, mock_stream_repository, existing_stream):
        """Test updating stream_name to its current value is allowed."""
        # Arrange
        updates = {'stream_name': 'Original Stream'}  # Same as current
        
        mock_stream_repository.get_by_id.return_value = existing_stream
        # Should not check for duplicates when name hasn't changed
        mock_stream_repository.update.return_value = existing_stream

        # Act
        result = use_case.execute(stream_id=1, updates=updates)

        # Assert
        assert result.stream_name == 'Original Stream'
        # Uniqueness check should still be called (use case doesn't optimize this)
        mock_stream_repository.update.assert_called_once()
