"""Comprehensive tests for all Course use cases.

This file tests create, update, delete, list, assign/unassign lecturer use cases.
"""

import pytest
from unittest.mock import Mock, patch

from academic_structure.domain.entities.course import Course
from academic_structure.domain.entities.program import Program
from academic_structure.domain.exceptions import (
    CourseNotFoundError,
    CourseCodeAlreadyExistsError,
    CourseCannotBeDeletedError,
    ValidationError,
    LecturerNotFoundError,
    LecturerInactiveError
)
from academic_structure.application.use_cases.course import (
    CreateCourseUseCase,
    UpdateCourseUseCase,
    DeleteCourseUseCase,
    ListCoursesUseCase,
    ListUnassignedCoursesUseCase,
    AssignLecturerUseCase,
    UnassignLecturerUseCase
)
from academic_structure.application.dto import CourseDTO


# ============================================================================
# CREATE COURSE TESTS
# ============================================================================

class TestCreateCourseUseCase:
    """Test cases for CreateCourseUseCase."""

    @pytest.fixture
    def mock_course_repository(self):
        return Mock()

    @pytest.fixture
    def mock_program_repository(self):
        return Mock()

    @pytest.fixture
    def use_case(self, mock_course_repository, mock_program_repository):
        return CreateCourseUseCase(mock_course_repository, mock_program_repository)

    def test_create_course_with_valid_data(self, use_case, mock_course_repository,
                                          mock_program_repository):
        """Test creating a course with valid data."""
        data = {
            'course_code': 'CS201',
            'course_name': 'Data Structures',
            'program_id': 1,
            'department_name': 'Computer Science'
        }
        
        program = Program(1, 'CS Program', 'CSC', 'CS', True)
        course = Course(1, 'Data Structures', 'CS201', 1, 'Computer Science', None)
        
        mock_program_repository.get_by_id.return_value = program
        mock_course_repository.exists_by_code.return_value = False
        mock_course_repository.create.return_value = course

        result = use_case.execute(data)

        assert isinstance(result, CourseDTO)
        assert result.course_code == 'CS201'
        assert result.course_name == 'Data Structures'

    def test_create_course_normalizes_code_to_uppercase(self, use_case, mock_course_repository,
                                                        mock_program_repository):
        """Test that course_code is normalized to uppercase."""
        data = {
            'course_code': 'cs201',
            'course_name': 'Test Course',
            'program_id': 1,
            'department_name': 'Computer Science'
        }
        
        program = Program(1, 'CS Program', 'CSC', 'Computer Science', True)
        course = Course(1, 'Test Course', 'CS201', 1, 'Computer Science', None)
        
        mock_program_repository.get_by_id.return_value = program
        mock_course_repository.exists_by_code.return_value = False
        mock_course_repository.create.return_value = course

        result = use_case.execute(data)

        assert result.course_code == 'CS201'
        mock_course_repository.exists_by_code.assert_called_once_with('CS201')

    def test_create_course_with_invalid_code_format(self, use_case):
        """Test that invalid course_code format raises ValidationError."""
        invalid_codes = ['AB', 'ABCDE123', 'A2C123', '12345']
        
        for invalid_code in invalid_codes:
            data = {
                'course_code': invalid_code,
                'course_name': 'Test Course',
                'program_id': 1,
                'department_name': 'Test'
            }
            
            with pytest.raises(ValidationError):
                use_case.execute(data)

    def test_create_course_with_duplicate_code(self, use_case, mock_course_repository,
                                               mock_program_repository):
        """Test creating course with duplicate code raises error."""
        data = {
            'course_code': 'CS201',
            'course_name': 'Data Structures',
            'program_id': 1,
            'department_name': 'Computer Science'
        }


# ============================================================================
# UPDATE COURSE TESTS
# ============================================================================

class TestUpdateCourseUseCase:
    """Test cases for UpdateCourseUseCase."""

    @pytest.fixture
    def mock_course_repository(self):
        return Mock()

    @pytest.fixture
    def use_case(self, mock_course_repository):
        return UpdateCourseUseCase(mock_course_repository)

    @pytest.fixture
    def existing_course(self):
        return Course(1, 'Data Structures', 'CS201', 1, 'CS', None)

    def test_update_course_name(self, use_case, mock_course_repository, existing_course):
        """Test updating course_name successfully."""
        updates = {'course_name': 'Advanced Data Structures'}
        updated_course = Course(1, 'Advanced Data Structures', 'CS201', 1, 'CS', None)
        
        mock_course_repository.get_by_id.return_value = existing_course
        mock_course_repository.update.return_value = updated_course

        result = use_case.execute(course_id=1, updates=updates)

        assert result.course_name == 'Advanced Data Structures'
        assert result.course_code == 'CS201'  # Unchanged

    def test_update_course_code_raises_error(self, use_case, mock_course_repository, existing_course):
        """Test that attempting to change course_code raises ValidationError."""
        updates = {'course_code': 'CS301'}
        
        mock_course_repository.get_by_id.return_value = existing_course

        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(course_id=1, updates=updates)
        
        assert 'course_code' in str(exc_info.value).lower()
        assert 'cannot be changed' in str(exc_info.value).lower()


# ============================================================================
# DELETE COURSE TESTS
# ============================================================================

class TestDeleteCourseUseCase:
    """Test cases for DeleteCourseUseCase."""

    @pytest.fixture
    def mock_course_repository(self):
        return Mock()

    @pytest.fixture
    def use_case(self, mock_course_repository):
        return DeleteCourseUseCase(mock_course_repository)

    @pytest.fixture
    def existing_course(self):
        return Course(1, 'Data Structures', 'CS201', 1, 'CS', None)

    def test_delete_course_successfully(self, use_case, mock_course_repository, existing_course):
        """Test deleting a course successfully when no sessions scheduled."""
        mock_course_repository.get_by_id.return_value = existing_course
        mock_course_repository.can_be_deleted.return_value = True

        result = use_case.execute(course_id=1)

        assert result is None
        mock_course_repository.delete.assert_called_once_with(1)

    def test_delete_course_with_sessions(self, use_case, mock_course_repository, existing_course):
        """Test that course with sessions cannot be deleted."""
        mock_course_repository.get_by_id.return_value = existing_course
        mock_course_repository.can_be_deleted.return_value = False
        mock_course_repository.count_sessions.return_value = 3

        with pytest.raises(CourseCannotBeDeletedError) as exc_info:
            use_case.execute(course_id=1)
        
        assert '3' in str(exc_info.value)
        mock_course_repository.delete.assert_not_called()


# ============================================================================
# LIST COURSES TESTS
# ============================================================================

class TestListCoursesUseCase:
    """Test cases for ListCoursesUseCase."""

    @pytest.fixture
    def mock_course_repository(self):
        return Mock()

    @pytest.fixture
    def mock_program_repository(self):
        return Mock()

    @pytest.fixture
    def use_case(self, mock_course_repository, mock_program_repository):
        return ListCoursesUseCase(mock_course_repository, mock_program_repository)

    def test_list_all_courses(self, use_case, mock_course_repository, mock_program_repository):
        """Test listing all courses without filters."""
        courses = [
            Course(1, 'Data Structures', 'CS201', 1, 'CS', None),
            Course(2, 'Algorithms', 'CS301', 1, 'CS', None),
        ]
        
        mock_course_repository.list_by_program.return_value = courses
        mock_program_repository.get_by_id.return_value = Mock(program_code='CSC')

        result = use_case.execute()

        assert len(result) == 2
        assert all(isinstance(dto, CourseDTO) for dto in result)
        mock_course_repository.list_by_program.assert_called_once_with(program_id=None)

    def test_list_courses_by_program(self, use_case, mock_course_repository):
        """Test listing courses filtered by program."""
        courses = [Course(1, 'Data Structures', 'CS201', 1, 'CS', None)]
        
        mock_course_repository.list_by_program.return_value = courses

        result = use_case.execute(program_id=1)

        assert len(result) == 1
        mock_course_repository.list_by_program.assert_called_once_with(1)


class TestListUnassignedCoursesUseCase:
    """Test cases for ListUnassignedCoursesUseCase."""

    @pytest.fixture
    def mock_course_repository(self):
        return Mock()

    @pytest.fixture
    def mock_program_repository(self):
        return Mock()

    @pytest.fixture
    def use_case(self, mock_course_repository, mock_program_repository):
        return ListUnassignedCoursesUseCase(mock_course_repository, mock_program_repository)

    def test_list_unassigned_courses(self, use_case, mock_course_repository):
        """Test listing courses without lecturers."""
        courses = [
            Course(1, 'CS201', 'Unassigned Course 1', 1, 'CS', None),
            Course(2, 'CS202', 'Unassigned Course 2', 1, 'CS', None),
        ]
        
        mock_course_repository.list_unassigned.return_value = courses

        result = use_case.execute()

        assert len(result) == 2
        assert all(dto.lecturer_id is None for dto in result)
        mock_course_repository.list_unassigned.assert_called_once()


# ============================================================================
# ASSIGN/UNASSIGN LECTURER TESTS
# ============================================================================

class TestAssignLecturerUseCase:
    """Test cases for AssignLecturerUseCase."""

    @pytest.fixture
    def mock_course_repository(self):
        return Mock()

    @pytest.fixture
    def use_case(self, mock_course_repository):
        return AssignLecturerUseCase(mock_course_repository)

    @pytest.fixture
    def existing_course(self):
        return Course(1, 'Data Structures', 'CS201', 1, 'CS', None)

    @patch('user_management.infrastructure.orm.django_models.LecturerProfile')
    def test_assign_lecturer_success(self, mock_lecturer_profile_class, use_case,
                                     mock_course_repository, existing_course):
        """Test assigning a lecturer to a course successfully."""
        # Mock active lecturer
        mock_lecturer = Mock()
        mock_lecturer.user.is_active = True
        mock_lecturer.user.get_full_name.return_value = 'Dr. Smith'
        mock_lecturer_profile_class.objects.select_related.return_value.get.return_value = mock_lecturer
        
        updated_course = Course(1, 'Data Structures', 'CS201', 1, 'CS', 10)
        
        mock_course_repository.get_by_id.return_value = existing_course
        mock_course_repository.update.return_value = updated_course

        result = use_case.execute(course_id=1, lecturer_id=10)

        assert result.lecturer_id == 10
        assert result.lecturer_name == 'Dr. Smith'

    def test_assign_nonexistent_lecturer_raises_error(self, use_case, mock_course_repository,
                                                      existing_course):
        """Test that assigning nonexistent lecturer raises LecturerNotFoundError."""
        # Import the real exception class first, before patching
        from user_management.infrastructure.orm.django_models import LecturerProfile
        
        # Now patch and configure mock to raise the real DoesNotExist exception
        with patch('user_management.infrastructure.orm.django_models.LecturerProfile') as mock_lp:
            mock_lp.DoesNotExist = LecturerProfile.DoesNotExist
            mock_lp.objects.select_related.return_value.get.side_effect = LecturerProfile.DoesNotExist
            
            mock_course_repository.get_by_id.return_value = existing_course

            with pytest.raises(LecturerNotFoundError):
                use_case.execute(course_id=1, lecturer_id=999)


class TestUnassignLecturerUseCase:
    """Test cases for UnassignLecturerUseCase."""

    @pytest.fixture
    def mock_course_repository(self):
        return Mock()

    @pytest.fixture
    def use_case(self, mock_course_repository):
        return UnassignLecturerUseCase(mock_course_repository)

    @pytest.fixture
    def course_with_lecturer(self):
        return Course(1, 'Data Structures', 'CS201', 1, 'CS', 10)

    def test_unassign_lecturer_success(self, use_case, mock_course_repository, course_with_lecturer):
        """Test unassigning a lecturer from a course successfully."""
        updated_course = Course(1, 'Data Structures', 'CS201', 1, 'CS', None)
        
        mock_course_repository.get_by_id.return_value = course_with_lecturer
        mock_course_repository.update.return_value = updated_course

        result = use_case.execute(course_id=1)

        assert result.lecturer_id is None
        assert result.lecturer_name is None
        mock_course_repository.update.assert_called_once()
