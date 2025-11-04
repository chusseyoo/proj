"""Tests for GetProgramUseCase and GetProgramByCodeUseCase."""

import pytest
from unittest.mock import Mock

from academic_structure.domain.entities.program import Program
from academic_structure.domain.exceptions import ProgramNotFoundError
from academic_structure.application.use_cases.program import (
    GetProgramUseCase,
    GetProgramByCodeUseCase
)
from academic_structure.application.dto import ProgramDTO


class TestGetProgramUseCase:
    """Test cases for GetProgramUseCase."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock ProgramRepository."""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_repository):
        """Create GetProgramUseCase with mocked repository."""
        return GetProgramUseCase(mock_repository)

    def test_get_program_by_id_success(self, use_case, mock_repository):
        """Test retrieving a program by ID successfully."""
        # Arrange
        program = Program(
            program_id=1,
            program_name='Bachelor of Science in Computer Science',
            program_code='CSC',
            department_name='Computer Science',
            has_streams=True
        )
        
        mock_repository.get_by_id.return_value = program

        # Act
        result = use_case.execute(program_id=1)

        # Assert
        assert isinstance(result, ProgramDTO)
        assert result.program_id == 1
        assert result.program_name == 'Bachelor of Science in Computer Science'
        assert result.program_code == 'CSC'
        assert result.department_name == 'Computer Science'
        assert result.has_streams is True
        
        mock_repository.get_by_id.assert_called_once_with(1)

    def test_get_program_by_id_not_found(self, use_case, mock_repository):
        """Test that non-existent program raises ProgramNotFoundError."""
        # Arrange
        mock_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ProgramNotFoundError) as exc_info:
            use_case.execute(program_id=999)
        
        assert '999' in str(exc_info.value)
        mock_repository.get_by_id.assert_called_once_with(999)

    def test_get_program_with_different_ids(self, use_case, mock_repository):
        """Test retrieving programs with different IDs."""
        program_ids = [1, 5, 100, 999]
        
        for pid in program_ids:
            program = Program(
                program_id=pid,
                program_name=f'Program {pid}',
                program_code='TST',
                department_name='Test',
                has_streams=False
            )
            
            mock_repository.get_by_id.return_value = program
            
            result = use_case.execute(program_id=pid)
            
            assert result.program_id == pid
            mock_repository.get_by_id.assert_called_with(pid)


class TestGetProgramByCodeUseCase:
    """Test cases for GetProgramByCodeUseCase."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock ProgramRepository."""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_repository):
        """Create GetProgramByCodeUseCase with mocked repository."""
        return GetProgramByCodeUseCase(mock_repository)

    def test_get_program_by_code_success(self, use_case, mock_repository):
        """Test retrieving a program by code successfully."""
        # Arrange
        program = Program(
            program_id=1,
            program_name='Bachelor of Arts in English',
            program_code='ENG',
            department_name='English',
            has_streams=False
        )
        
        mock_repository.get_by_code.return_value = program

        # Act
        result = use_case.execute(program_code='ENG')

        # Assert
        assert isinstance(result, ProgramDTO)
        assert result.program_id == 1
        assert result.program_code == 'ENG'
        assert result.program_name == 'Bachelor of Arts in English'
        
        mock_repository.get_by_code.assert_called_once_with('ENG')

    def test_get_program_by_code_not_found(self, use_case, mock_repository):
        """Test that non-existent program code raises ProgramNotFoundError."""
        # Arrange
        mock_repository.get_by_code.return_value = None

        # Act & Assert
        with pytest.raises(ProgramNotFoundError) as exc_info:
            use_case.execute(program_code='XYZ')
        
        assert 'XYZ' in str(exc_info.value)
        mock_repository.get_by_code.assert_called_once_with('XYZ')

    def test_get_program_by_code_passes_code_as_is(self, use_case, mock_repository):
        """Test that program_code is passed as-is to repository (case handling done at repo level)."""
        # Arrange
        program = Program(
            program_id=1,
            program_name='Test Program',
            program_code='CSC',
            department_name='Computer Science',
            has_streams=True
        )
        
        mock_repository.get_by_code.return_value = program

        # Test with lowercase - use case passes it as-is, repository handles case-insensitivity
        result = use_case.execute(program_code='csc')
        
        # Use case should pass code as-is
        mock_repository.get_by_code.assert_called_with('csc')
        assert result.program_code == 'CSC'  # Entity returned has uppercase

    def test_get_program_by_code_with_whitespace(self, use_case, mock_repository):
        """Test get program by code with whitespace (normalization done at repo level)."""
        # Arrange
        program = Program(
            program_id=1,
            program_name='Test Program',
            program_code='ENG',
            department_name='Engineering',
            has_streams=False
        )
        
        mock_repository.get_by_code.return_value = program

        # Act - use case passes code as-is
        result = use_case.execute(program_code='  ENG  ')

        # Assert - passed as-is to repository
        mock_repository.get_by_code.assert_called_once_with('  ENG  ')
        assert result.program_code == 'ENG'
