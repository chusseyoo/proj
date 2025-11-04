"""Tests for UpdateProgramUseCase."""

import pytest
from unittest.mock import Mock

from academic_structure.domain.entities.program import Program
from academic_structure.domain.exceptions import (
    ProgramNotFoundError,
    ValidationError
)
from academic_structure.application.use_cases.program import UpdateProgramUseCase
from academic_structure.application.dto import ProgramDTO


class TestUpdateProgramUseCase:
    """Test cases for UpdateProgramUseCase."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock ProgramRepository."""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_repository):
        """Create UpdateProgramUseCase with mocked repository."""
        return UpdateProgramUseCase(mock_repository)

    @pytest.fixture
    def existing_program(self):
        """Create an existing program for update tests."""
        return Program(
            program_id=1,
            program_name='Original Program',
            program_code='ORP',
            department_name='Original Department',
            has_streams=False
        )

    def test_update_program_name(self, use_case, mock_repository, existing_program):
        """Test updating program_name successfully."""
        # Arrange
        updates = {'program_name': 'Updated Program Name'}
        
        updated_program = Program(
            program_id=1,
            program_name='Updated Program Name',
            program_code='ORP',
            department_name='Original Department',
            has_streams=False
        )
        
        mock_repository.get_by_id.return_value = existing_program
        mock_repository.update.return_value = updated_program

        # Act
        result = use_case.execute(program_id=1, updates=updates)

        # Assert
        assert isinstance(result, ProgramDTO)
        assert result.program_name == 'Updated Program Name'
        assert result.program_code == 'ORP'  # Unchanged
        
        mock_repository.get_by_id.assert_called_once_with(1)
        mock_repository.update.assert_called_once()

    def test_update_department_name(self, use_case, mock_repository, existing_program):
        """Test updating department_name successfully."""
        # Arrange
        updates = {'department_name': 'New Department'}
        
        updated_program = Program(
            program_id=1,
            program_name='Original Program',
            program_code='ORP',
            department_name='New Department',
            has_streams=False
        )
        
        mock_repository.get_by_id.return_value = existing_program
        mock_repository.update.return_value = updated_program

        # Act
        result = use_case.execute(program_id=1, updates=updates)

        # Assert
        assert result.department_name == 'New Department'

    def test_update_has_streams(self, use_case, mock_repository, existing_program):
        """Test updating has_streams flag successfully."""
        # Arrange
        updates = {'has_streams': True}
        
        updated_program = Program(
            program_id=1,
            program_name='Original Program',
            program_code='ORP',
            department_name='Original Department',
            has_streams=True
        )
        
        mock_repository.get_by_id.return_value = existing_program
        mock_repository.update.return_value = updated_program

        # Act
        result = use_case.execute(program_id=1, updates=updates)

        # Assert
        assert result.has_streams is True

    def test_update_multiple_fields(self, use_case, mock_repository, existing_program):
        """Test updating multiple fields at once."""
        # Arrange
        updates = {
            'program_name': 'Completely New Program',
            'department_name': 'New Department',
            'has_streams': True
        }
        
        updated_program = Program(
            program_id=1,
            program_name='Completely New Program',
            program_code='ORP',
            department_name='New Department',
            has_streams=True
        )
        
        mock_repository.get_by_id.return_value = existing_program
        mock_repository.update.return_value = updated_program

        # Act
        result = use_case.execute(program_id=1, updates=updates)

        # Assert
        assert result.program_name == 'Completely New Program'
        assert result.department_name == 'New Department'
        assert result.has_streams is True
        assert result.program_code == 'ORP'  # Unchanged

    def test_update_program_not_found(self, use_case, mock_repository):
        """Test updating non-existent program raises ProgramNotFoundError."""
        # Arrange
        mock_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ProgramNotFoundError) as exc_info:
            use_case.execute(program_id=999, updates={'program_name': 'Test'})
        
        assert '999' in str(exc_info.value)
        mock_repository.update.assert_not_called()

    def test_update_program_code_raises_error(self, use_case, mock_repository, existing_program):
        """Test that attempting to change program_code raises ValidationError."""
        # Arrange
        updates = {'program_code': 'NEW'}
        
        mock_repository.get_by_id.return_value = existing_program

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(program_id=1, updates=updates)
        
        assert 'program_code' in str(exc_info.value).lower()
        assert 'cannot be changed' in str(exc_info.value).lower()
        mock_repository.update.assert_not_called()

    def test_update_program_with_short_name(self, use_case, mock_repository, existing_program):
        """Test that program_name less than 5 characters raises ValidationError."""
        # Arrange
        updates = {'program_name': 'Test'}  # 4 characters
        
        mock_repository.get_by_id.return_value = existing_program

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(program_id=1, updates=updates)
        
        assert 'program_name' in str(exc_info.value).lower()
        assert '5' in str(exc_info.value)
        mock_repository.update.assert_not_called()

    def test_update_program_with_long_name(self, use_case, mock_repository, existing_program):
        """Test that program_name longer than 200 characters raises ValidationError."""
        # Arrange
        updates = {'program_name': 'A' * 201}
        
        mock_repository.get_by_id.return_value = existing_program

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(program_id=1, updates=updates)
        
        assert 'program_name' in str(exc_info.value).lower()
        assert '200' in str(exc_info.value)
        mock_repository.update.assert_not_called()

    def test_update_program_with_short_department_name(self, use_case, mock_repository, existing_program):
        """Test that department_name less than 3 characters raises ValidationError."""
        # Arrange
        updates = {'department_name': 'CS'}  # 2 characters
        
        mock_repository.get_by_id.return_value = existing_program

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(program_id=1, updates=updates)
        
        assert 'department_name' in str(exc_info.value).lower()
        assert '3' in str(exc_info.value)
        mock_repository.update.assert_not_called()

    def test_update_program_with_long_department_name(self, use_case, mock_repository, existing_program):
        """Test that department_name longer than 150 characters raises ValidationError."""
        # Arrange
        updates = {'department_name': 'D' * 151}
        
        mock_repository.get_by_id.return_value = existing_program

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(program_id=1, updates=updates)
        
        assert 'department_name' in str(exc_info.value).lower()
        assert '150' in str(exc_info.value)
        mock_repository.update.assert_not_called()

    def test_update_program_trims_whitespace(self, use_case, mock_repository, existing_program):
        """Test that whitespace is trimmed from updated fields."""
        # Arrange
        updates = {
            'program_name': '  Trimmed Program  ',
            'department_name': '  Trimmed Dept  '
        }
        
        updated_program = Program(
            program_id=1,
            program_name='Trimmed Program',
            program_code='ORP',
            department_name='Trimmed Dept',
            has_streams=False
        )
        
        mock_repository.get_by_id.return_value = existing_program
        mock_repository.update.return_value = updated_program

        # Act
        result = use_case.execute(program_id=1, updates=updates)

        # Assert
        assert result.program_name == 'Trimmed Program'
        assert result.department_name == 'Trimmed Dept'

    def test_update_program_with_empty_updates(self, use_case, mock_repository, existing_program):
        """Test updating program with empty updates dictionary."""
        # Arrange
        updates = {}
        
        mock_repository.get_by_id.return_value = existing_program
        mock_repository.update.return_value = existing_program

        # Act
        result = use_case.execute(program_id=1, updates=updates)

        # Assert
        assert result.program_id == 1
        assert result.program_name == existing_program.program_name
        mock_repository.update.assert_called_once()
