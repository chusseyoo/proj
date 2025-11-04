"""Tests for CreateStreamUseCase."""

import pytest
from unittest.mock import Mock

from academic_structure.domain.entities.program import Program
from academic_structure.domain.entities.stream import Stream
from academic_structure.domain.exceptions import (
    ValidationError,
    ProgramNotFoundError,
    StreamAlreadyExistsError,
    StreamNotAllowedError
)
from academic_structure.application.use_cases.stream import CreateStreamUseCase
from academic_structure.application.dto import StreamDTO


class TestCreateStreamUseCase:
    """Test cases for CreateStreamUseCase."""

    @pytest.fixture
    def mock_stream_repository(self):
        """Create a mock StreamRepository."""
        return Mock()

    @pytest.fixture
    def mock_program_repository(self):
        """Create a mock ProgramRepository."""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_stream_repository, mock_program_repository):
        """Create CreateStreamUseCase with mocked repositories."""
        return CreateStreamUseCase(mock_stream_repository, mock_program_repository)

    @pytest.fixture
    def program_with_streams(self):
        """Program that allows streams."""
        return Program(
            program_id=1,
            program_name='Bachelor of Science',
            program_code='BSC',
            department_name='Science',
            has_streams=True
        )

    @pytest.fixture
    def program_without_streams(self):
        """Program that does not allow streams."""
        return Program(
            program_id=2,
            program_name='Bachelor of Arts',
            program_code='BAR',
            department_name='Arts',
            has_streams=False
        )

    def test_create_stream_with_valid_data(self, use_case, mock_stream_repository, 
                                           mock_program_repository, program_with_streams):
        """Test creating a stream with valid data."""
        # Arrange
        data = {
            'stream_name': 'Stream A',
            'program_id': 1,
            'year_of_study': 2
        }
        
        created_stream = Stream(
            stream_id=1,
            stream_name='Stream A',
            program_id=1,
            year_of_study=2
        )
        
        mock_program_repository.get_by_id.return_value = program_with_streams
        mock_stream_repository.exists_by_program_and_name.return_value = False
        mock_stream_repository.create.return_value = created_stream

        # Act
        result = use_case.execute(data)

        # Assert
        assert isinstance(result, StreamDTO)
        assert result.stream_id == 1
        assert result.stream_name == 'Stream A'
        assert result.program_id == 1
        assert result.year_of_study == 2
        
        mock_program_repository.get_by_id.assert_called_once_with(1)
        mock_stream_repository.exists_by_program_and_name.assert_called_once_with(1, 'Stream A')
        mock_stream_repository.create.assert_called_once()

    def test_create_stream_with_missing_required_fields(self, use_case):
        """Test that missing required fields raises ValidationError."""
        # Missing stream_name
        data = {
            'program_id': 1,
            'year_of_study': 2
        }

        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(data)
        
        assert 'stream_name' in str(exc_info.value)

    def test_create_stream_with_short_name(self, use_case):
        """Test that stream_name less than 1 character raises ValidationError."""
        data = {
            'stream_name': '',  # Empty
            'program_id': 1,
            'year_of_study': 1
        }

        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(data)
        
        assert 'stream_name' in str(exc_info.value).lower()

    def test_create_stream_with_long_name(self, use_case):
        """Test that stream_name longer than 50 characters raises ValidationError."""
        data = {
            'stream_name': 'A' * 51,  # 51 characters
            'program_id': 1,
            'year_of_study': 1
        }

        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(data)
        
        assert 'stream_name' in str(exc_info.value).lower()
        assert '50' in str(exc_info.value)

    def test_create_stream_with_invalid_year_below_range(self, use_case):
        """Test that year_of_study < 1 raises ValidationError."""
        data = {
            'stream_name': 'Stream A',
            'program_id': 1,
            'year_of_study': 0  # Invalid
        }

        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(data)
        
        assert 'year_of_study' in str(exc_info.value).lower()

    def test_create_stream_with_invalid_year_above_range(self, use_case):
        """Test that year_of_study > 4 raises ValidationError."""
        data = {
            'stream_name': 'Stream A',
            'program_id': 1,
            'year_of_study': 5  # Invalid
        }

        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(data)
        
        assert 'year_of_study' in str(exc_info.value).lower()

    def test_create_stream_with_all_valid_years(self, use_case, mock_stream_repository,
                                                mock_program_repository, program_with_streams):
        """Test creating streams with all valid year values (1-4)."""
        mock_program_repository.get_by_id.return_value = program_with_streams
        mock_stream_repository.exists_by_program_and_name.return_value = False
        
        for year in range(1, 5):
            data = {
                'stream_name': f'Year {year}',
                'program_id': 1,
                'year_of_study': year
            }
            
            created_stream = Stream(
                stream_id=year,
                stream_name=f'Year {year}',
                program_id=1,
                year_of_study=year
            )
            
            mock_stream_repository.create.return_value = created_stream
            
            result = use_case.execute(data)
            
            assert result.year_of_study == year

    def test_create_stream_for_nonexistent_program(self, use_case, mock_program_repository):
        """Test that creating stream for nonexistent program raises ProgramNotFoundError."""
        data = {
            'stream_name': 'Stream A',
            'program_id': 999,
            'year_of_study': 1
        }
        
        mock_program_repository.get_by_id.return_value = None

        with pytest.raises(ProgramNotFoundError) as exc_info:
            use_case.execute(data)
        
        assert '999' in str(exc_info.value)
        mock_program_repository.get_by_id.assert_called_once_with(999)

    def test_create_stream_for_program_without_streams_flag(self, use_case, mock_stream_repository,
                                                           mock_program_repository, program_without_streams):
        """Test that creating stream for program with has_streams=False raises StreamNotAllowedError."""
        data = {
            'stream_name': 'Stream A',
            'program_id': 2,
            'year_of_study': 1
        }
        
        mock_program_repository.get_by_id.return_value = program_without_streams

        with pytest.raises(StreamNotAllowedError) as exc_info:
            use_case.execute(data)
        
        assert 'BAR' in str(exc_info.value)  # program_code
        mock_stream_repository.create.assert_not_called()

    def test_create_stream_with_duplicate_name_in_program(self, use_case, mock_stream_repository,
                                                          mock_program_repository, program_with_streams):
        """Test that duplicate stream name in same program raises StreamAlreadyExistsError."""
        data = {
            'stream_name': 'Stream A',
            'program_id': 1,
            'year_of_study': 1
        }
        
        mock_program_repository.get_by_id.return_value = program_with_streams
        mock_stream_repository.exists_by_program_and_name.return_value = True

        with pytest.raises(StreamAlreadyExistsError) as exc_info:
            use_case.execute(data)
        
        error_msg = str(exc_info.value)
        assert 'Stream A' in error_msg
        assert 'BSC' in error_msg  # program_code
        mock_stream_repository.create.assert_not_called()

    def test_create_stream_trims_whitespace(self, use_case, mock_stream_repository,
                                           mock_program_repository, program_with_streams):
        """Test that whitespace is trimmed from stream_name."""
        data = {
            'stream_name': '  Stream A  ',
            'program_id': 1,
            'year_of_study': 1
        }
        
        created_stream = Stream(
            stream_id=1,
            stream_name='Stream A',
            program_id=1,
            year_of_study=1
        )
        
        mock_program_repository.get_by_id.return_value = program_with_streams
        mock_stream_repository.exists_by_program_and_name.return_value = False
        mock_stream_repository.create.return_value = created_stream

        # Act
        result = use_case.execute(data)

        # Assert
        assert result.stream_name == 'Stream A'
        mock_stream_repository.exists_by_program_and_name.assert_called_once_with(1, 'Stream A')
