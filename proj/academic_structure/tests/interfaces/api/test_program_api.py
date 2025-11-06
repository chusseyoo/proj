"""Tests for Program API endpoints."""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from academic_structure.infrastructure.orm.django_models import Program


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
def sample_programs(db):
    """Fixture for multiple programs."""
    programs = [
        Program.objects.create(
            program_name='Bachelor of Computer Science',
            program_code='BCS',
            department_name='Computer Science',
            has_streams=True
        ),
        Program.objects.create(
            program_name='Bachelor of Engineering',
            program_code='BEG',
            department_name='Engineering',
            has_streams=False
        ),
        Program.objects.create(
            program_name='Bachelor of Information Technology',
            program_code='BIT',
            department_name='Computer Science',
            has_streams=True
        ),
    ]
    return programs


@pytest.mark.django_db
class TestProgramListAPI:
    """Test cases for GET /programs/ endpoint."""

    def test_list_programs_as_admin(self, api_client, admin_user, sample_programs):
        """Test listing programs as admin user."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-list')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert response.data['total_count'] == 3
        assert len(response.data['results']) == 3

    def test_list_programs_as_lecturer(self, api_client, lecturer_user, sample_programs):
        """Test listing programs as lecturer user."""
        api_client.force_authenticate(user=lecturer_user)
        url = reverse('program-list')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_count'] == 3

    def test_list_programs_unauthenticated(self, api_client, sample_programs):
        """Test listing programs without authentication fails."""
        url = reverse('program-list')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_filter_programs_by_department(self, api_client, admin_user, sample_programs):
        """Test filtering programs by department_name."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-list')
        
        response = api_client.get(url, {'department_name': 'Computer Science'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_count'] == 2  # BCS and BIT

    def test_filter_programs_by_has_streams(self, api_client, admin_user, sample_programs):
        """Test filtering programs by has_streams flag."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-list')
        
        response = api_client.get(url, {'has_streams': 'true'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_count'] == 2  # BCS and BIT

    def test_search_programs(self, api_client, admin_user, sample_programs):
        """Test searching programs by name or code."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-list')
        
        response = api_client.get(url, {'search': 'Computer'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_count'] >= 1

    def test_pagination(self, api_client, admin_user, sample_programs):
        """Test pagination parameters."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-list')
        
        response = api_client.get(url, {'page': 1, 'page_size': 2})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        assert response.data['has_next'] is True


@pytest.mark.django_db
class TestProgramCreateAPI:
    """Test cases for POST /programs/ endpoint."""

    def test_create_program_as_admin(self, api_client, admin_user):
        """Test creating a program as admin."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-list')
        data = {
            'program_name': 'Bachelor of Science',
            'program_code': 'BSC',
            'department_name': 'Science',
            'has_streams': False
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['program_code'] == 'BSC'
        assert response.data['program_name'] == 'Bachelor of Science'
        assert Program.objects.filter(program_code='BSC').exists()

    def test_create_program_as_lecturer_fails(self, api_client, lecturer_user):
        """Test creating a program as lecturer fails."""
        api_client.force_authenticate(user=lecturer_user)
        url = reverse('program-list')
        data = {
            'program_name': 'Bachelor of Science',
            'program_code': 'BSC',
            'department_name': 'Science',
            'has_streams': False
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_duplicate_program_code(self, api_client, admin_user, sample_program):
        """Test creating program with duplicate code fails."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-list')
        data = {
            'program_name': 'Another Program',
            'program_code': 'BCS',  # Duplicate
            'department_name': 'Computer Science',
            'has_streams': False
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_create_program_invalid_code(self, api_client, admin_user):
        """Test creating program with invalid code format."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-list')
        data = {
            'program_name': 'Test Program',
            'program_code': 'BC',  # Too short
            'department_name': 'Testing Department',
            'has_streams': False
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestProgramRetrieveAPI:
    """Test cases for GET /programs/{id}/ endpoint."""

    def test_retrieve_program_by_id(self, api_client, admin_user, sample_program):
        """Test retrieving a program by ID."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-detail', kwargs={'pk': sample_program.program_id})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['program_id'] == sample_program.program_id
        assert response.data['program_code'] == 'BCS'

    def test_retrieve_nonexistent_program(self, api_client, admin_user):
        """Test retrieving non-existent program returns 404."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-detail', kwargs={'pk': 9999})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_program_by_code(self, api_client, admin_user, sample_program):
        """Test retrieving a program by code."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-by-code', kwargs={'program_code': 'BCS'})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['program_code'] == 'BCS'

    def test_retrieve_program_by_code_case_insensitive(self, api_client, admin_user, sample_program):
        """Test retrieving program by code is case-insensitive."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-by-code', kwargs={'program_code': 'bcs'})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['program_code'] == 'BCS'


@pytest.mark.django_db
class TestProgramUpdateAPI:
    """Test cases for PATCH /programs/{id}/ endpoint."""

    def test_update_program_as_admin(self, api_client, admin_user, sample_program):
        """Test updating a program as admin."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-detail', kwargs={'pk': sample_program.program_id})
        data = {
            'program_name': 'Updated Program Name',
            'department_name': 'Updated Department'
        }
        
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['program_name'] == 'Updated Program Name'
        
        sample_program.refresh_from_db()
        assert sample_program.program_name == 'Updated Program Name'

    def test_update_program_as_lecturer_fails(self, api_client, lecturer_user, sample_program):
        """Test updating program as lecturer fails."""
        api_client.force_authenticate(user=lecturer_user)
        url = reverse('program-detail', kwargs={'pk': sample_program.program_id})
        data = {'program_name': 'Updated'}
        
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_program_code_fails(self, api_client, admin_user, sample_program):
        """Test that updating program_code is not allowed."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-detail', kwargs={'pk': sample_program.program_id})
        data = {'program_code': 'NEW'}
        
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestProgramDeleteAPI:
    """Test cases for DELETE /programs/{id}/ endpoint."""

    def test_delete_program_as_admin(self, api_client, admin_user, sample_program):
        """Test deleting a program as admin."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-detail', kwargs={'pk': sample_program.program_id})
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Program.objects.filter(program_id=sample_program.program_id).exists()

    def test_delete_program_as_lecturer_fails(self, api_client, lecturer_user, sample_program):
        """Test deleting program as lecturer fails."""
        api_client.force_authenticate(user=lecturer_user)
        url = reverse('program-detail', kwargs={'pk': sample_program.program_id})
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_nonexistent_program(self, api_client, admin_user):
        """Test deleting non-existent program returns 404."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-detail', kwargs={'pk': 9999})
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
