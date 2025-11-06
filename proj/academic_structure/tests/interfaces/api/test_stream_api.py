"""Tests for Stream API endpoints."""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from academic_structure.infrastructure.orm.django_models import Program, Stream


@pytest.fixture
def api_client():
    """Fixture providing API client."""
    return APIClient()


@pytest.fixture
def program_with_streams(db):
    """Fixture for program with streams enabled."""
    return Program.objects.create(
        program_name='Bachelor of Computer Science',
        program_code='BCS',
        department_name='Computer Science',
        has_streams=True
    )


@pytest.fixture
def program_without_streams(db):
    """Fixture for program without streams."""
    return Program.objects.create(
        program_name='Bachelor of Engineering',
        program_code='BEG',
        department_name='Engineering',
        has_streams=False
    )


@pytest.fixture
def sample_streams(db, program_with_streams):
    """Fixture for multiple streams."""
    streams = [
        Stream.objects.create(
            stream_name='Stream A',
            program=program_with_streams,
            year_of_study=1
        ),
        Stream.objects.create(
            stream_name='Stream B',
            program=program_with_streams,
            year_of_study=1
        ),
        Stream.objects.create(
            stream_name='Stream A',
            program=program_with_streams,
            year_of_study=2
        ),
    ]
    return streams


@pytest.mark.django_db
class TestStreamListAPI:
    """Test cases for GET /programs/{program_id}/streams/ endpoint."""

    def test_list_streams_as_admin(self, api_client, admin_user, program_with_streams, sample_streams):
        """Test listing streams under a program as admin."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-streams-list', kwargs={'program_pk': program_with_streams.program_id})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_list_streams_as_lecturer(self, api_client, lecturer_user, program_with_streams, sample_streams):
        """Test listing streams as lecturer."""
        api_client.force_authenticate(user=lecturer_user)
        url = reverse('program-streams-list', kwargs={'program_pk': program_with_streams.program_id})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_filter_streams_by_year(self, api_client, admin_user, program_with_streams, sample_streams):
        """Test filtering streams by year_of_study."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-streams-list', kwargs={'program_pk': program_with_streams.program_id})
        
        response = api_client.get(url, {'year_of_study': 1})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2  # Stream A and B for year 1

    def test_list_streams_nonexistent_program(self, api_client, admin_user):
        """Test listing streams for non-existent program returns 404."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-streams-list', kwargs={'program_pk': 9999})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestStreamCreateAPI:
    """Test cases for POST /programs/{program_id}/streams/ endpoint."""

    def test_create_stream_as_admin(self, api_client, admin_user, program_with_streams):
        """Test creating a stream as admin."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-streams-list', kwargs={'program_pk': program_with_streams.program_id})
        data = {
            'stream_name': 'Stream C',
            'year_of_study': 1
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['stream_name'] == 'Stream C'
        assert response.data['year_of_study'] == 1
        assert Stream.objects.filter(stream_name='Stream C', program=program_with_streams).exists()

    def test_create_stream_as_lecturer_fails(self, api_client, lecturer_user, program_with_streams):
        """Test creating stream as lecturer fails."""
        api_client.force_authenticate(user=lecturer_user)
        url = reverse('program-streams-list', kwargs={'program_pk': program_with_streams.program_id})
        data = {
            'stream_name': 'Stream C',
            'year_of_study': 1
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_stream_for_program_without_streams(self, api_client, admin_user, program_without_streams):
        """Test creating stream for program with has_streams=False fails."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-streams-list', kwargs={'program_pk': program_without_streams.program_id})
        data = {
            'stream_name': 'Stream A',
            'year_of_study': 1
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_duplicate_stream(self, api_client, admin_user, program_with_streams, sample_streams):
        """Test creating duplicate stream fails."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-streams-list', kwargs={'program_pk': program_with_streams.program_id})
        data = {
            'stream_name': 'Stream A',
            'year_of_study': 1  # Already exists
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_create_stream_invalid_year(self, api_client, admin_user, program_with_streams):
        """Test creating stream with invalid year fails."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('program-streams-list', kwargs={'program_pk': program_with_streams.program_id})
        data = {
            'stream_name': 'Stream X',
            'year_of_study': 5  # Invalid (must be 1-4)
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestStreamRetrieveAPI:
    """Test cases for GET /streams/{id}/ endpoint."""

    def test_retrieve_stream_by_id(self, api_client, admin_user, sample_streams):
        """Test retrieving a stream by ID."""
        api_client.force_authenticate(user=admin_user)
        stream = sample_streams[0]
        url = reverse('stream-detail', kwargs={'pk': stream.stream_id})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['stream_id'] == stream.stream_id
        assert response.data['stream_name'] == 'Stream A'
        assert 'program_code' in response.data

    def test_retrieve_nonexistent_stream(self, api_client, admin_user):
        """Test retrieving non-existent stream returns 404."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('stream-detail', kwargs={'pk': 9999})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestStreamUpdateAPI:
    """Test cases for PATCH /streams/{id}/ endpoint."""

    def test_update_stream_as_admin(self, api_client, admin_user, sample_streams):
        """Test updating a stream as admin."""
        api_client.force_authenticate(user=admin_user)
        stream = sample_streams[0]
        url = reverse('stream-detail', kwargs={'pk': stream.stream_id})
        data = {
            'stream_name': 'Updated Stream Name'
        }
        
        response = api_client.patch(url, data, format='json')
        
        if response.status_code != status.HTTP_200_OK:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['stream_name'] == 'Updated Stream Name'
        
        stream.refresh_from_db()
        assert stream.stream_name == 'Updated Stream Name'

    def test_update_stream_as_lecturer_fails(self, api_client, lecturer_user, sample_streams):
        """Test updating stream as lecturer fails."""
        api_client.force_authenticate(user=lecturer_user)
        stream = sample_streams[0]
        url = reverse('stream-detail', kwargs={'pk': stream.stream_id})
        data = {'stream_name': 'Updated'}
        
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_stream_year(self, api_client, admin_user, sample_streams):
        """Test updating stream year_of_study."""
        api_client.force_authenticate(user=admin_user)
        stream = sample_streams[0]
        url = reverse('stream-detail', kwargs={'pk': stream.stream_id})
        data = {'year_of_study': 3}
        
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['year_of_study'] == 3

    def test_update_stream_to_duplicate(self, api_client, admin_user, sample_streams):
        """Test updating stream to create duplicate fails."""
        api_client.force_authenticate(user=admin_user)
        stream = sample_streams[1]  # Stream B, year 1
        url = reverse('stream-detail', kwargs={'pk': stream.stream_id})
        data = {
            'stream_name': 'Stream A'  # Already exists for year 1
        }
        
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.django_db
class TestStreamDeleteAPI:
    """Test cases for DELETE /streams/{id}/ endpoint."""

    def test_delete_stream_as_admin(self, api_client, admin_user, sample_streams):
        """Test deleting a stream as admin."""
        api_client.force_authenticate(user=admin_user)
        stream = sample_streams[0]
        stream_id = stream.stream_id
        url = reverse('stream-detail', kwargs={'pk': stream_id})
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Stream.objects.filter(stream_id=stream_id).exists()

    def test_delete_stream_as_lecturer_fails(self, api_client, lecturer_user, sample_streams):
        """Test deleting stream as lecturer fails."""
        api_client.force_authenticate(user=lecturer_user)
        stream = sample_streams[0]
        url = reverse('stream-detail', kwargs={'pk': stream.stream_id})
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_nonexistent_stream(self, api_client, admin_user):
        """Test deleting non-existent stream returns 404."""
        api_client.force_authenticate(user=admin_user)
        url = reverse('stream-detail', kwargs={'pk': 9999})
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
