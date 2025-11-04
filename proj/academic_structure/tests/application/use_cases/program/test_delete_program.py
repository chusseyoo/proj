"""Tests for DeleteProgramUseCase."""

import pytest
from unittest.mock import Mock

from academic_structure.domain.entities.program import Program
from academic_structure.domain.exceptions import (
    ProgramNotFoundError,
    ProgramCannotBeDeletedError
)
from academic_structure.application.use_cases.program import DeleteProgramUseCase


class TestDeleteProgramUseCase:
    """Test cases for DeleteProgramUseCase."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock ProgramRepository."""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_repository):
        """Create DeleteProgramUseCase with mocked repository."""
        return DeleteProgramUseCase(mock_repository)

    @pytest.fixture
    def existing_program(self):
        """Create an existing program for delete tests."""
        return Program(
            program_id=1,
            program_name='Program to Delete',
            program_code='PTD',
            department_name='Test Department',
            has_streams=False
        )

    def test_delete_program_successfully(self, use_case, mock_repository, existing_program):
        """Test deleting a program successfully when no dependencies exist."""
        # Arrange
        mock_repository.get_by_id.return_value = existing_program
        mock_repository.can_be_deleted.return_value = True

        # Act
        result = use_case.execute(program_id=1)

        # Assert
        assert result is None
        mock_repository.get_by_id.assert_called_once_with(1)
        mock_repository.can_be_deleted.assert_called_once_with(1)
        mock_repository.delete.assert_called_once_with(1)

    def test_delete_program_not_found(self, use_case, mock_repository):
        """Test deleting non-existent program raises ProgramNotFoundError."""
        # Arrange
        mock_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ProgramNotFoundError) as exc_info:
            use_case.execute(program_id=999)
        
        assert '999' in str(exc_info.value)
        mock_repository.can_be_deleted.assert_not_called()
        mock_repository.delete.assert_not_called()

    def test_delete_program_with_students(self, use_case, mock_repository, existing_program):
        """Test that program with students cannot be deleted."""
        # Arrange
        mock_repository.get_by_id.return_value = existing_program
        mock_repository.can_be_deleted.return_value = False
        mock_repository.students_count.return_value = 5
        mock_repository.courses_count.return_value = 0

        # Act & Assert
        with pytest.raises(ProgramCannotBeDeletedError) as exc_info:
            use_case.execute(program_id=1)
        
        error_message = str(exc_info.value)
        assert 'PTD' in error_message  # program_code
        assert '5' in error_message
        assert 'student' in error_message.lower()
        
        mock_repository.delete.assert_not_called()

    def test_delete_program_with_courses(self, use_case, mock_repository, existing_program):
        """Test that program with courses cannot be deleted."""
        # Arrange
        mock_repository.get_by_id.return_value = existing_program
        mock_repository.can_be_deleted.return_value = False
        mock_repository.students_count.return_value = 0
        mock_repository.courses_count.return_value = 3

        # Act & Assert
        with pytest.raises(ProgramCannotBeDeletedError) as exc_info:
            use_case.execute(program_id=1)
        
        error_message = str(exc_info.value)
        assert 'PTD' in error_message  # program_code
        assert '3' in error_message
        assert 'course' in error_message.lower()
        
        mock_repository.delete.assert_not_called()

    def test_delete_program_with_students_and_courses(self, use_case, mock_repository, existing_program):
        """Test that program with both students and courses cannot be deleted."""
        # Arrange
        mock_repository.get_by_id.return_value = existing_program
        mock_repository.can_be_deleted.return_value = False
        mock_repository.students_count.return_value = 10
        mock_repository.courses_count.return_value = 7

        # Act & Assert
        with pytest.raises(ProgramCannotBeDeletedError) as exc_info:
            use_case.execute(program_id=1)
        
        error_message = str(exc_info.value)
        assert 'PTD' in error_message  # program_code
        assert '10' in error_message
        assert '7' in error_message
        assert 'student' in error_message.lower()
        assert 'course' in error_message.lower()
        
        mock_repository.delete.assert_not_called()

    def test_delete_program_checks_dependencies_before_deletion(self, use_case, mock_repository, existing_program):
        """Test that use case checks can_be_deleted before attempting deletion."""
        # Arrange
        mock_repository.get_by_id.return_value = existing_program
        mock_repository.can_be_deleted.return_value = True

        # Act
        use_case.execute(program_id=1)

        # Assert - verify order of operations
        assert mock_repository.get_by_id.called
        assert mock_repository.can_be_deleted.called
        assert mock_repository.delete.called
        
        # Verify can_be_deleted is called before delete
        call_order = [call[0] for call in mock_repository.method_calls]
        can_be_deleted_idx = call_order.index('can_be_deleted')
        delete_idx = call_order.index('delete')
        assert can_be_deleted_idx < delete_idx

    def test_delete_program_different_ids(self, use_case, mock_repository):
        """Test deleting programs with different IDs."""
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
            mock_repository.can_be_deleted.return_value = True
            
            use_case.execute(program_id=pid)
            
            mock_repository.get_by_id.assert_called_with(pid)
            mock_repository.can_be_deleted.assert_called_with(pid)
            mock_repository.delete.assert_called_with(pid)
