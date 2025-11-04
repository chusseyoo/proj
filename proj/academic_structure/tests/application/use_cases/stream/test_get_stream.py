"""Tests for GetStreamUseCase and ListStreamsByProgramUseCase."""

import pytest
from unittest.mock import Mock

from academic_structure.domain.entities.stream import Stream
from academic_structure.domain.entities.program import Program
from academic_structure.domain.exceptions import StreamNotFoundError, ProgramNotFoundError
from academic_structure.application.use_cases.stream import (
    GetStreamUseCase,
    ListStreamsByProgramUseCase
)
from academic_structure.application.dto import StreamDTO


class TestGetStreamUseCase:
    """Test cases for GetStreamUseCase."""

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
        """Create GetStreamUseCase with mocked repositories."""
        return GetStreamUseCase(mock_stream_repository, mock_program_repository)

    def test_get_stream_by_id_success(self, use_case, mock_stream_repository):
        """Test retrieving a stream by ID successfully."""
        # Arrange
        stream = Stream(
            stream_id=1,
            stream_name='Stream A',
            program_id=1,
            year_of_study=2
        )
        
        mock_stream_repository.get_by_id.return_value = stream

        # Act
        result = use_case.execute(stream_id=1)

        # Assert
        assert isinstance(result, StreamDTO)
        assert result.stream_id == 1
        assert result.stream_name == 'Stream A'
        assert result.program_id == 1
        assert result.year_of_study == 2
        assert result.program_code is None  # No enrichment
        
        mock_stream_repository.get_by_id.assert_called_once_with(1)

    def test_get_stream_by_id_not_found(self, use_case, mock_stream_repository):
        """Test that non-existent stream raises StreamNotFoundError."""
        # Arrange
        mock_stream_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(StreamNotFoundError) as exc_info:
            use_case.execute(stream_id=999)
        
        assert '999' in str(exc_info.value)
        mock_stream_repository.get_by_id.assert_called_once_with(999)

    def test_get_stream_with_program_code_enrichment(self, use_case, mock_stream_repository,
                                                     mock_program_repository):
        """Test retrieving stream with program_code enrichment."""
        # Arrange
        stream = Stream(
            stream_id=1,
            stream_name='Stream A',
            program_id=5,
            year_of_study=3
        )
        
        program = Program(
            program_id=5,
            program_name='Test Program',
            program_code='TST',
            department_name='Test',
            has_streams=True
        )
        
        mock_stream_repository.get_by_id.return_value = stream
        mock_program_repository.get_by_id.return_value = program

        # Act
        result = use_case.execute(stream_id=1, include_program_code=True)

        # Assert
        assert result.stream_id == 1
        assert result.program_code == 'TST'
        
        mock_stream_repository.get_by_id.assert_called_once_with(1)
        mock_program_repository.get_by_id.assert_called_once_with(5)

    def test_get_stream_without_enrichment(self, use_case, mock_stream_repository,
                                          mock_program_repository):
        """Test that program repository is not called when enrichment not requested."""
        # Arrange
        stream = Stream(
            stream_id=1,
            stream_name='Stream B',
            program_id=2,
            year_of_study=1
        )
        
        mock_stream_repository.get_by_id.return_value = stream

        # Act
        result = use_case.execute(stream_id=1, include_program_code=False)

        # Assert
        assert result.program_code is None
        mock_program_repository.get_by_id.assert_not_called()


class TestListStreamsByProgramUseCase:
    """Test cases for ListStreamsByProgramUseCase."""

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
        """Create ListStreamsByProgramUseCase with mocked repositories."""
        return ListStreamsByProgramUseCase(mock_stream_repository, mock_program_repository)

    def test_list_streams_by_program(self, use_case, mock_stream_repository, mock_program_repository):
        """Test listing all streams for a program."""
        # Arrange
        streams = [
            Stream(1, 'Stream A', 1, 1),
            Stream(2, 'Stream B', 1, 2),
            Stream(3, 'Stream C', 1, 3),
        ]
        
        mock_stream_repository.list_by_program.return_value = streams

        # Act
        result = use_case.execute(program_id=1)

        # Assert
        assert len(result) == 3
        assert all(isinstance(dto, StreamDTO) for dto in result)
        assert result[0].stream_id == 1
        assert result[1].stream_id == 2
        assert result[2].stream_id == 3
        
        # Program repository not called when enrichment not requested
        mock_program_repository.get_by_id.assert_not_called()
        mock_stream_repository.list_by_program.assert_called_once_with(1)

    def test_list_streams_by_program_returns_empty_for_nonexistent(self, use_case, mock_stream_repository):
        """Test that listing streams for nonexistent program returns empty list."""
        # Arrange
        mock_stream_repository.list_by_program.return_value = []

        # Act
        result = use_case.execute(program_id=999)
        
        # Assert
        assert result == []
        mock_stream_repository.list_by_program.assert_called_once_with(999)

    def test_list_streams_filtered_by_year(self, use_case, mock_stream_repository, mock_program_repository):
        """Test listing streams filtered by year_of_study."""
        # Arrange
        year_2_streams = [
            Stream(2, 'Year 2 Stream A', 1, 2),
            Stream(3, 'Year 2 Stream B', 1, 2),
        ]
        
        mock_stream_repository.list_by_program_and_year.return_value = year_2_streams

        # Act
        result = use_case.execute(program_id=1, year_of_study=2)

        # Assert
        assert len(result) == 2
        assert all(dto.year_of_study == 2 for dto in result)
        assert result[0].stream_id == 2
        assert result[1].stream_id == 3
        
        # Should use list_by_program_and_year when year filter provided
        mock_stream_repository.list_by_program_and_year.assert_called_once_with(1, 2)
        mock_stream_repository.list_by_program.assert_not_called()

    def test_list_streams_with_program_code_enrichment(self, use_case, mock_stream_repository,
                                                       mock_program_repository):
        """Test listing streams with program_code enrichment."""
        # Arrange
        program = Program(5, 'Computer Science', 'CSC', 'CS Dept', True)
        streams = [
            Stream(1, 'Stream A', 5, 1),
            Stream(2, 'Stream B', 5, 2),
        ]
        
        mock_program_repository.get_by_id.return_value = program
        mock_stream_repository.list_by_program.return_value = streams

        # Act
        result = use_case.execute(program_id=5, include_program_code=True)

        # Assert
        assert len(result) == 2
        assert all(dto.program_code == 'CSC' for dto in result)

    def test_list_streams_empty_result(self, use_case, mock_stream_repository, mock_program_repository):
        """Test listing streams when program has no streams."""
        # Arrange
        program = Program(1, 'Test Program', 'TST', 'Test', True)
        mock_program_repository.get_by_id.return_value = program
        mock_stream_repository.list_by_program.return_value = []

        # Act
        result = use_case.execute(program_id=1)

        # Assert
        assert result == []
        assert isinstance(result, list)

    def test_list_streams_preserves_order(self, use_case, mock_stream_repository, mock_program_repository):
        """Test that stream order from repository is preserved."""
        # Arrange
        program = Program(1, 'Test Program', 'TST', 'Test', True)
        streams = [
            Stream(3, 'Stream C', 1, 3),
            Stream(1, 'Stream A', 1, 1),
            Stream(2, 'Stream B', 1, 2),
        ]
        
        mock_program_repository.get_by_id.return_value = program
        mock_stream_repository.list_by_program.return_value = streams

        # Act
        result = use_case.execute(program_id=1)

        # Assert
        assert result[0].stream_id == 3
        assert result[1].stream_id == 1
        assert result[2].stream_id == 2
