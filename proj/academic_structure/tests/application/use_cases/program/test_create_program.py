"""Tests for CreateProgramUseCase."""

import pytest
from unittest.mock import Mock

from academic_structure.domain.entities.program import Program
from academic_structure.domain.exceptions import (
    ValidationError,
    ProgramCodeAlreadyExistsError
)
from academic_structure.application.use_cases.program import CreateProgramUseCase
from academic_structure.application.dto import ProgramDTO


class TestCreateProgramUseCase:
    """Test cases for CreateProgramUseCase."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock ProgramRepository."""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_repository):
        """Create CreateProgramUseCase with mocked repository."""
        return CreateProgramUseCase(mock_repository)

    def test_create_program_with_valid_data(self, use_case, mock_repository):
        """Test creating a program with valid data."""
        # Arrange
        data = {
            'program_name': 'Bachelor of Science in Computer Science',
            'program_code': 'CSC',
            'department_name': 'Computer Science',
            'has_streams': True
        }
        
        created_program = Program(
            program_id=1,
            program_name='Bachelor of Science in Computer Science',
            program_code='CSC',
            department_name='Computer Science',
            has_streams=True
        )
        
        mock_repository.exists_by_code.return_value = False
        mock_repository.create.return_value = created_program

        # Act
        result = use_case.execute(data)

        # Assert
        assert isinstance(result, ProgramDTO)
        assert result.program_id == 1
        assert result.program_name == 'Bachelor of Science in Computer Science'
        assert result.program_code == 'CSC'
        assert result.department_name == 'Computer Science'
        assert result.has_streams is True
        
        mock_repository.exists_by_code.assert_called_once_with('CSC')
        mock_repository.create.assert_called_once()

    def test_create_program_normalizes_code_to_uppercase(self, use_case, mock_repository):
        """Test that program_code is normalized to uppercase."""
        # Arrange
        data = {
            'program_name': 'Test Program',
            'program_code': 'eng',  # lowercase
            'department_name': 'Engineering',
            'has_streams': False
        }
        
        created_program = Program(
            program_id=1,
            program_name='Test Program',
            program_code='ENG',
            department_name='Engineering',
            has_streams=False
        )
        
        mock_repository.exists_by_code.return_value = False
        mock_repository.create.return_value = created_program

        # Act
        result = use_case.execute(data)

        # Assert
        assert result.program_code == 'ENG'
        mock_repository.exists_by_code.assert_called_once_with('ENG')

    def test_create_program_with_missing_required_fields(self, use_case):
        """Test that missing required fields raises ValidationError."""
        # Missing program_name
        data = {
            'program_code': 'CSC',
            'department_name': 'Computer Science',
            'has_streams': True
        }

        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(data)
        
        assert 'program_name' in str(exc_info.value)

    def test_create_program_with_invalid_code_format(self, use_case):
        """Test that invalid program_code format raises ValidationError."""
        invalid_codes = [
            'AB',      # Too short
            'ABCD',    # Too long
            'A2C',     # Contains digit
            'ab c',    # Contains space
            '123',     # Only digits
        ]

        for invalid_code in invalid_codes:
            data = {
                'program_name': 'Test Program',
                'program_code': invalid_code,
                'department_name': 'Test',
                'has_streams': False
            }

            with pytest.raises(ValidationError) as exc_info:
                use_case.execute(data)
            
            assert 'program_code' in str(exc_info.value).lower()

    def test_create_program_with_short_name(self, use_case):
        """Test that program_name less than 5 characters raises ValidationError."""
        data = {
            'program_name': 'Test',  # 4 characters
            'program_code': 'TST',
            'department_name': 'Testing',
            'has_streams': False
        }

        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(data)
        
        assert 'program_name' in str(exc_info.value).lower()
        assert '5' in str(exc_info.value)

    def test_create_program_with_long_name(self, use_case):
        """Test that program_name longer than 200 characters raises ValidationError."""
        data = {
            'program_name': 'A' * 201,  # 201 characters
            'program_code': 'TST',
            'department_name': 'Testing',
            'has_streams': False
        }

        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(data)
        
        assert 'program_name' in str(exc_info.value).lower()
        assert '200' in str(exc_info.value)

    def test_create_program_with_short_department_name(self, use_case):
        """Test that department_name less than 3 characters raises ValidationError."""
        data = {
            'program_name': 'Test Program',
            'program_code': 'TST',
            'department_name': 'CS',  # 2 characters
            'has_streams': False
        }

        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(data)
        
        assert 'department_name' in str(exc_info.value).lower()
        assert '3' in str(exc_info.value)

    def test_create_program_with_long_department_name(self, use_case):
        """Test that department_name longer than 150 characters raises ValidationError."""
        data = {
            'program_name': 'Test Program',
            'program_code': 'TST',
            'department_name': 'D' * 151,  # 151 characters
            'has_streams': False
        }

        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(data)
        
        assert 'department_name' in str(exc_info.value).lower()
        assert '150' in str(exc_info.value)

    def test_create_program_with_duplicate_code(self, use_case, mock_repository):
        """Test that duplicate program_code raises ProgramCodeAlreadyExistsError."""
        data = {
            'program_name': 'New Program',
            'program_code': 'CSC',
            'department_name': 'Computer Science',
            'has_streams': False
        }
        
        mock_repository.exists_by_code.return_value = True

        with pytest.raises(ProgramCodeAlreadyExistsError) as exc_info:
            use_case.execute(data)
        
        assert 'CSC' in str(exc_info.value)
        mock_repository.exists_by_code.assert_called_once_with('CSC')
        mock_repository.create.assert_not_called()

    def test_create_program_trims_whitespace(self, use_case, mock_repository):
        """Test that whitespace is trimmed from string fields."""
        data = {
            'program_name': '  Test Program  ',
            'program_code': '  TST  ',
            'department_name': '  Testing  ',
            'has_streams': False
        }
        
        created_program = Program(
            program_id=1,
            program_name='Test Program',
            program_code='TST',
            department_name='Testing',
            has_streams=False
        )
        
        mock_repository.exists_by_code.return_value = False
        mock_repository.create.return_value = created_program

        # Act
        result = use_case.execute(data)

        # Assert
        assert result.program_name == 'Test Program'
        assert result.program_code == 'TST'
        assert result.department_name == 'Testing'
