"""Tests for Course get use cases (GetCourseUseCase and GetCourseByCodeUseCase)."""

import pytest
from unittest.mock import Mock, patch

from academic_structure.domain.entities.course import Course
from academic_structure.domain.entities.program import Program
from academic_structure.domain.exceptions import CourseNotFoundError
from academic_structure.application.use_cases.course import (
    GetCourseUseCase,
    GetCourseByCodeUseCase
)
from academic_structure.application.dto import CourseDTO


class TestGetCourseUseCase:
    """Test cases for GetCourseUseCase."""

    @pytest.fixture
    def mock_course_repository(self):
        """Create a mock CourseRepository."""
        return Mock()

    @pytest.fixture
    def mock_program_repository(self):
        """Create a mock ProgramRepository."""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_course_repository, mock_program_repository):
        """Create GetCourseUseCase with mocked repositories."""
        return GetCourseUseCase(mock_course_repository, mock_program_repository)

    def test_get_course_by_id_success(self, use_case, mock_course_repository):
        """Test retrieving a course by ID successfully."""
        # Arrange
        course = Course(
            course_id=1,
            course_code='CS201',
            course_name='Data Structures',
            program_id=1,
            department_name='Computer Science',
            lecturer_id=None
        )
        
        mock_course_repository.get_by_id.return_value = course

        # Act
        result = use_case.execute(course_id=1)

        # Assert
        assert isinstance(result, CourseDTO)
        assert result.course_id == 1
        assert result.course_code == 'CS201'
        assert result.course_name == 'Data Structures'
        assert result.program_id == 1
        assert result.department_name == 'Computer Science'
        assert result.lecturer_id is None
        assert result.program_code is None
        assert result.lecturer_name is None
        
        mock_course_repository.get_by_id.assert_called_once_with(1)

    def test_get_course_by_id_not_found(self, use_case, mock_course_repository):
        """Test that non-existent course raises CourseNotFoundError."""
        # Arrange
        mock_course_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(CourseNotFoundError) as exc_info:
            use_case.execute(course_id=999)
        
        assert '999' in str(exc_info.value)
        mock_course_repository.get_by_id.assert_called_once_with(999)

    def test_get_course_with_program_code_enrichment(self, use_case, mock_course_repository,
                                                     mock_program_repository):
        """Test retrieving course with program_code enrichment."""
        # Arrange
        course = Course(1, 'Data Structures', 'CS201', 5, 'CS', None)
        program = Program(5, 'Computer Science', 'CSC', 'CS Dept', True)
        
        mock_course_repository.get_by_id.return_value = course
        mock_program_repository.get_by_id.return_value = program

        # Act
        result = use_case.execute(course_id=1, include_program_code=True)

        # Assert
        assert result.program_code == 'CSC'
        mock_program_repository.get_by_id.assert_called_once_with(5)

    @patch('user_management.infrastructure.orm.django_models.LecturerProfile')
    def test_get_course_with_lecturer_name_enrichment(self, mock_lecturer_profile_class,
                                                       use_case, mock_course_repository):
        """Test retrieving course with lecturer_name enrichment (cross-context)."""
        # Arrange
        course = Course(1, 'Data Structures', 'CS201', 1, 'CS', 10)
        
        # Mock LecturerProfile query
        mock_lecturer = Mock()
        mock_lecturer.user.get_full_name.return_value = 'Dr. John Smith'
        mock_lecturer_profile_class.objects.select_related.return_value.get.return_value = mock_lecturer
        
        mock_course_repository.get_by_id.return_value = course

        # Act
        result = use_case.execute(course_id=1, include_lecturer_name=True)

        # Assert
        assert result.lecturer_name == 'Dr. John Smith'
        mock_lecturer_profile_class.objects.select_related.assert_called_once_with('user')


class TestGetCourseByCodeUseCase:
    """Test cases for GetCourseByCodeUseCase."""

    @pytest.fixture
    def mock_course_repository(self):
        """Create a mock CourseRepository."""
        return Mock()

    @pytest.fixture
    def mock_program_repository(self):
        """Create a mock ProgramRepository."""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_course_repository, mock_program_repository):
        """Create GetCourseByCodeUseCase with mocked repositories."""
        return GetCourseByCodeUseCase(mock_course_repository, mock_program_repository)

    def test_get_course_by_code_success(self, use_case, mock_course_repository):
        """Test retrieving a course by code successfully."""
        # Arrange
        course = Course(
            course_id=1,
            course_code='ENG301',
            course_name='Advanced English',
            program_id=2,
            department_name='English',
            lecturer_id=None
        )
        
        mock_course_repository.get_by_code.return_value = course

        # Act
        result = use_case.execute(course_code='ENG301')

        # Assert
        assert isinstance(result, CourseDTO)
        assert result.course_id == 1
        assert result.course_code == 'ENG301'
        assert result.course_name == 'Advanced English'
        
        mock_course_repository.get_by_code.assert_called_once_with('ENG301')

    def test_get_course_by_code_not_found(self, use_case, mock_course_repository):
        """Test that non-existent course code raises CourseNotFoundError."""
        # Arrange
        mock_course_repository.get_by_code.return_value = None

        # Act & Assert
        with pytest.raises(CourseNotFoundError) as exc_info:
            use_case.execute(course_code='XYZ999')
        
        assert 'XYZ999' in str(exc_info.value)
        mock_course_repository.get_by_code.assert_called_once_with('XYZ999')

    def test_get_course_by_code_passes_as_is(self, use_case, mock_course_repository):
        """Test that course_code is passed as-is (case handling at repo level)."""
        # Arrange
        course = Course(1, 'Data Structures', 'CS201', 1, 'CS', None)
        mock_course_repository.get_by_code.return_value = course

        # Act
        result = use_case.execute(course_code='cs201')

        # Assert
        # Use case passes code as-is, repository handles case-insensitivity
        mock_course_repository.get_by_code.assert_called_once_with('cs201')
        assert result.course_code == 'CS201'  # Entity has proper case
