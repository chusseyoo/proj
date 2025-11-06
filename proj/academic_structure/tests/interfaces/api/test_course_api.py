"""Tests for Course API endpoints."""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from academic_structure.infrastructure.orm.django_models import Program, Course
from user_management.infrastructure.orm.django_models import LecturerProfile


@pytest.fixture
def api_client():
    """Fixture providing API client."""
    return APIClient()


@pytest.fixture
def sample_program(db):
    """Fixture for sample program."""
    return Program.objects.create(
        program_name='Bachelor of Computer Science',
        program_code='BCS',
        department_name='Computer Science',
        has_streams=True
    )


@pytest.fixture
def lecturer_profile(db, lecturer_user):
    """Fixture for lecturer profile."""
    return LecturerProfile.objects.create(
        user=lecturer_user,
        department_name='Computer Science'
    )


@pytest.fixture
def sample_course(db, sample_program):
    """Fixture for sample course without lecturer."""
    return Course.objects.create(
        course_name='Data Structures',
        course_code='BCS201',
        program=sample_program,
        department_name='Computer Science',
        lecturer=None
    )


@pytest.fixture
def course_with_lecturer(db, sample_program, lecturer_profile):
    """Fixture for course with assigned lecturer."""
    return Course.objects.create(
        course_name='Algorithms',
        course_code='BCS301',
        program=sample_program,
        department_name='Computer Science',
        lecturer=lecturer_profile
    )


@pytest.fixture
def sample_courses(db, sample_program, lecturer_profile):
    """Fixture for multiple courses."""
    courses = [
        Course.objects.create(
            course_name='Data Structures',
            course_code='BCS201',
            program=sample_program,
            department_name='Computer Science',
            lecturer=lecturer_profile
        ),
        Course.objects.create(
            course_name='Algorithms',
            course_code='BCS301',
            program=sample_program,
            department_name='Computer Science',
            lecturer=None
        ),
        Course.objects.create(
            course_name='Database Systems',
            course_code='BCS401',
            program=sample_program,
            department_name='Computer Science',
            lecturer=lecturer_profile
        ),
    ]
    return courses


@pytest.mark.django_db
class TestCourseListAPI:
    """Test cases for GET /courses/ endpoint."""

    def test_list_courses_as_admin(self, api_client, admin_user, sample_courses):
        """Test listing courses as admin."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-list')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert response.data['total_count'] == 3

    def test_list_courses_as_lecturer(self, api_client, lecturer_user, sample_courses):
        """Test listing courses as lecturer."""
        api_client.force_authenticate(user=lecturer_user)
        url = reverse('course-list')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_count'] == 3

    def test_filter_courses_by_program(self, api_client, admin_user, sample_courses, sample_program):
        """Test filtering courses by program_id."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-list')
        
        response = api_client.get(url, {'program_id': sample_program.program_id})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_count'] == 3

    def test_filter_courses_by_lecturer(self, api_client, admin_user, sample_courses, lecturer_profile):
        """Test filtering courses by lecturer_id."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-list')
        
        response = api_client.get(url, {'lecturer_id': lecturer_profile.lecturer_id})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_count'] == 2  # CS201 and CS401

    def test_filter_courses_by_department(self, api_client, admin_user, sample_courses):
        """Test filtering courses by department_name."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-list')
        
        response = api_client.get(url, {'department_name': 'Computer Science'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_count'] == 3

    def test_search_courses(self, api_client, admin_user, sample_courses):
        """Test searching courses by code or name."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-list')
        
        response = api_client.get(url, {'q': 'Data'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_count'] >= 1


@pytest.mark.django_db
class TestCourseCreateAPI:
    """Test cases for POST /courses/ endpoint."""

    def test_create_course_as_admin(self, api_client, admin_user, sample_program):
        """Test creating a course as admin."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-list')
        data = {
            'course_code': 'BCS205',
            'course_name': 'Operating Systems',
            'program_id': sample_program.program_id,
            'department_name': 'Computer Science'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['course_code'] == 'BCS205'
        assert Course.objects.filter(course_code='BCS205').exists()

    def test_create_course_with_lecturer(self, api_client, admin_user, sample_program, lecturer_profile):
        """Test creating course with lecturer assignment."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-list')
        data = {
            'course_code': 'BCS205',
            'course_name': 'Operating Systems',
            'program_id': sample_program.program_id,
            'department_name': 'Computer Science',
            'lecturer_id': lecturer_profile.lecturer_id
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['lecturer_id'] == lecturer_profile.lecturer_id

    def test_create_course_as_lecturer_fails(self, api_client, lecturer_user, sample_program):
        """Test creating course as lecturer fails."""
        api_client.force_authenticate(user=lecturer_user)
        url = reverse('course-list')
        data = {
            'course_code': 'BCS205',
            'course_name': 'Operating Systems',
            'program_id': sample_program.program_id,
            'department_name': 'Computer Science'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_duplicate_course_code(self, api_client, admin_user, sample_course):
        """Test creating course with duplicate code fails."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-list')
        data = {
            'course_code': 'BCS201',  # Duplicate
            'course_name': 'Another Course',
            'program_id': sample_course.program.program_id,
            'department_name': 'Computer Science'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_create_course_invalid_code(self, api_client, admin_user, sample_program):
        """Test creating course with invalid code format."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-list')
        data = {
            'course_code': 'CS1',  # Invalid format
            'course_name': 'Test Course',
            'program_id': sample_program.program_id,
            'department_name': 'Computer Science'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_course_nonexistent_program(self, api_client, admin_user):
        """Test creating course with non-existent program fails."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-list')
        data = {
            'course_code': 'BCS205',
            'course_name': 'Test Course',
            'program_id': 9999,
            'department_name': 'Computer Science'
        }
        
        response = api_client.post(url, data, format='json')
        
        print(f"\nResponse status: {response.status_code}")
        print(f"Response data: {response.data}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCourseRetrieveAPI:
    """Test cases for GET /courses/{id}/ endpoint."""

    def test_retrieve_course_by_id(self, api_client, admin_user, sample_course):
        """Test retrieving a course by ID."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-detail', kwargs={'pk': sample_course.course_id})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['course_id'] == sample_course.course_id
        assert response.data['course_code'] == 'BCS201'

    def test_retrieve_course_with_enrichment(self, api_client, admin_user, course_with_lecturer):
        """Test retrieving course includes program_code and lecturer_name."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-detail', kwargs={'pk': course_with_lecturer.course_id})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'program_code' in response.data
        assert 'lecturer_name' in response.data

    def test_retrieve_nonexistent_course(self, api_client, admin_user):
        """Test retrieving non-existent course returns 404."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-detail', kwargs={'pk': 9999})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_course_by_code(self, api_client, admin_user, sample_course):
        """Test retrieving a course by code."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-by-code', kwargs={'course_code': 'BCS201'})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['course_code'] == 'BCS201'

    def test_retrieve_course_by_code_case_insensitive(self, api_client, admin_user, sample_course):
        """Test retrieving course by code is case-insensitive."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-by-code', kwargs={'course_code': 'bcs201'})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['course_code'] == 'BCS201'


@pytest.mark.django_db
class TestCourseUpdateAPI:
    """Test cases for PATCH /courses/{id}/ endpoint."""

    def test_update_course_as_admin(self, api_client, admin_user, sample_course):
        """Test updating a course as admin."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-detail', kwargs={'pk': sample_course.course_id})
        data = {
            'course_name': 'Updated Course Name',
            'department_name': 'Updated Department'
        }
        
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['course_name'] == 'Updated Course Name'

    def test_update_course_as_lecturer_fails(self, api_client, lecturer_user, sample_course):
        """Test updating course as lecturer fails."""
        api_client.force_authenticate(user=lecturer_user)
        url = reverse('course-detail', kwargs={'pk': sample_course.course_id})
        data = {'course_name': 'Updated'}
        
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_course_code_fails(self, api_client, admin_user, sample_course):
        """Test that updating course_code is not allowed."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-detail', kwargs={'pk': sample_course.course_id})
        data = {'course_code': 'BCS999'}
        
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCourseDeleteAPI:
    """Test cases for DELETE /courses/{id}/ endpoint."""

    def test_delete_course_as_admin(self, api_client, admin_user, sample_course):
        """Test deleting a course as admin."""
        api_client.force_authenticate(user=admin_user)
        course_id = sample_course.course_id
        url = reverse('course-detail', kwargs={'pk': course_id})
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Course.objects.filter(course_id=course_id).exists()

    def test_delete_course_as_lecturer_fails(self, api_client, lecturer_user, sample_course):
        """Test deleting course as lecturer fails."""
        api_client.force_authenticate(user=lecturer_user)
        url = reverse('course-detail', kwargs={'pk': sample_course.course_id})
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAssignLecturerAPI:
    """Test cases for POST /courses/{id}/assign-lecturer/ endpoint."""

    def test_assign_lecturer_as_admin(self, api_client, admin_user, sample_course, lecturer_profile):
        """Test assigning lecturer to course as admin."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-assign-lecturer', kwargs={'pk': sample_course.course_id})
        data = {'lecturer_id': lecturer_profile.lecturer_id}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['lecturer_id'] == lecturer_profile.lecturer_id
        assert 'lecturer_name' in response.data
        
        sample_course.refresh_from_db()
        assert sample_course.lecturer_id == lecturer_profile.lecturer_id

    def test_assign_lecturer_as_lecturer_fails(self, api_client, lecturer_user, sample_course, lecturer_profile):
        """Test assigning lecturer as lecturer fails."""
        api_client.force_authenticate(user=lecturer_user)
        url = reverse('course-assign-lecturer', kwargs={'pk': sample_course.course_id})
        data = {'lecturer_id': lecturer_profile.lecturer_id}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_assign_nonexistent_lecturer(self, api_client, admin_user, sample_course):
        """Test assigning non-existent lecturer fails."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-assign-lecturer', kwargs={'pk': sample_course.course_id})
        data = {'lecturer_id': 9999}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_assign_lecturer_to_nonexistent_course(self, api_client, admin_user, lecturer_profile):
        """Test assigning lecturer to non-existent course fails."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-assign-lecturer', kwargs={'pk': 9999})
        data = {'lecturer_id': lecturer_profile.lecturer_id}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestUnassignLecturerAPI:
    """Test cases for POST /courses/{id}/unassign-lecturer/ endpoint."""

    def test_unassign_lecturer_as_admin(self, api_client, admin_user, course_with_lecturer):
        """Test unassigning lecturer from course as admin."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-unassign-lecturer', kwargs={'pk': course_with_lecturer.course_id})
        
        response = api_client.post(url, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['lecturer_id'] is None
        assert response.data['lecturer_name'] is None
        
        course_with_lecturer.refresh_from_db()
        assert course_with_lecturer.lecturer is None

    def test_unassign_lecturer_as_lecturer_fails(self, api_client, lecturer_user, course_with_lecturer):
        """Test unassigning lecturer as lecturer fails."""
        api_client.force_authenticate(user=lecturer_user)
        url = reverse('course-unassign-lecturer', kwargs={'pk': course_with_lecturer.course_id})
        
        response = api_client.post(url, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unassign_from_nonexistent_course(self, api_client, admin_user):
        """Test unassigning from non-existent course fails."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('course-unassign-lecturer', kwargs={'pk': 9999})
        
        response = api_client.post(url, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
