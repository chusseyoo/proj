"""Tests for ListProgramsUseCase."""

import pytest
from unittest.mock import Mock

from academic_structure.domain.entities.program import Program
from academic_structure.application.use_cases.program import ListProgramsUseCase
from academic_structure.application.dto import ProgramDTO


class TestListProgramsUseCase:
    """Test cases for ListProgramsUseCase."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock ProgramRepository."""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_repository):
        """Create ListProgramsUseCase with mocked repository."""
        return ListProgramsUseCase(mock_repository)

    def test_list_all_programs(self, use_case, mock_repository):
        """Test listing all programs without filters."""
        # Arrange
        programs = [
            Program(1, 'Program 1', 'PR1', 'Dept 1', True),
            Program(2, 'Program 2', 'PR2', 'Dept 2', False),
            Program(3, 'Program 3', 'PR3', 'Dept 1', True),
        ]
        
        mock_repository.list_all.return_value = programs

        # Act
        result = use_case.execute()

        # Assert
        assert len(result) == 3
        assert all(isinstance(dto, ProgramDTO) for dto in result)
        assert result[0].program_id == 1
        assert result[1].program_id == 2
        assert result[2].program_id == 3
        
        mock_repository.list_all.assert_called_once()

    def test_list_programs_by_department(self, use_case, mock_repository):
        """Test listing programs filtered by department."""
        # Arrange
        programs = [
            Program(1, 'CS Program', 'CSC', 'Computer Science', True),
            Program(2, 'CS Advanced', 'CSA', 'Computer Science', False),
        ]
        
        mock_repository.list_by_department.return_value = programs

        # Act
        result = use_case.execute(department_name='Computer Science')

        # Assert
        assert len(result) == 2
        assert all(dto.department_name == 'Computer Science' for dto in result)
        
        mock_repository.list_by_department.assert_called_once_with('Computer Science')
        mock_repository.list_all.assert_not_called()

    def test_list_programs_with_streams(self, use_case, mock_repository):
        """Test listing programs that have streams."""
        # Arrange
        programs = [
            Program(1, 'Program with Streams', 'PWS', 'Dept 1', True),
            Program(3, 'Another Streamed', 'AST', 'Dept 2', True),
        ]
        
        mock_repository.list_with_streams.return_value = programs

        # Act
        result = use_case.execute(has_streams=True)

        # Assert
        assert len(result) == 2
        assert all(dto.has_streams is True for dto in result)
        
        mock_repository.list_with_streams.assert_called_once()
        mock_repository.list_all.assert_not_called()

    def test_list_programs_without_streams(self, use_case, mock_repository):
        """Test listing programs that don't have streams."""
        # Arrange
        programs = [
            Program(2, 'No Streams Program', 'NSP', 'Dept 1', False),
        ]
        
        mock_repository.list_without_streams.return_value = programs

        # Act
        result = use_case.execute(has_streams=False)

        # Assert
        assert len(result) == 1
        assert result[0].has_streams is False
        
        mock_repository.list_without_streams.assert_called_once()
        mock_repository.list_all.assert_not_called()

    def test_list_programs_with_combined_filters(self, use_case, mock_repository):
        """Test listing programs with both department and has_streams filters."""
        # Arrange
        # When both filters provided, department is queried first, then filtered by has_streams
        programs = [
            Program(1, 'CS with Streams', 'CSC', 'Computer Science', True),
            Program(2, 'CS without Streams', 'CSB', 'Computer Science', False),
        ]
        
        mock_repository.list_by_department.return_value = programs

        # Act
        result = use_case.execute(
            department_name='Computer Science',
            has_streams=True
        )

        # Assert
        assert len(result) == 1
        assert result[0].program_id == 1
        assert result[0].has_streams is True
        
        # Department queried first, then filtered in-memory
        mock_repository.list_by_department.assert_called_once_with('Computer Science')
        mock_repository.list_with_streams.assert_not_called()

    def test_list_programs_empty_result(self, use_case, mock_repository):
        """Test listing programs when no programs exist."""
        # Arrange
        mock_repository.list_all.return_value = []

        # Act
        result = use_case.execute()

        # Assert
        assert result == []
        assert isinstance(result, list)
        
        mock_repository.list_all.assert_called_once()

    def test_list_programs_preserves_order(self, use_case, mock_repository):
        """Test that program order from repository is preserved."""
        # Arrange
        programs = [
            Program(3, 'Program C', 'PRC', 'Dept C', False),
            Program(1, 'Program A', 'PRA', 'Dept A', True),
            Program(2, 'Program B', 'PRB', 'Dept B', False),
        ]
        
        mock_repository.list_all.return_value = programs

        # Act
        result = use_case.execute()

        # Assert
        assert result[0].program_id == 3
        assert result[1].program_id == 1
        assert result[2].program_id == 2
