import pytest
from rest_framework import status


@pytest.mark.django_db
def test_register_lecturer_success(api_client):
    url = "/api/users/register/lecturer"
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "password": "SecurePass123!",
        "department_name": "Computer Science",
    }

    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert "access_token" in body and "refresh_token" in body
    assert body["email"] == "john.doe@example.com"


@pytest.mark.django_db
def test_register_student_by_admin_success(api_client, admin_user, program, stream):
    # Authenticate as admin by forcing credentials on client
    api_client.force_authenticate(user=admin_user)

    url = "/api/users/register/student"
    data = {
        "first_name": "Jane",
        "last_name": "Student",
        "email": "jane.student@example.com",
        "student_id": "BCS/000002",
        "program_id": program.program_id,
        "stream_id": stream.stream_id,
        "year_of_study": 2,
    }

    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["student_id"] == "BCS/000002"
    assert body["email"] == "jane.student@example.com"


@pytest.mark.django_db
def test_register_student_non_admin_forbidden(api_client, lecturer_user, program, stream):
    api_client.force_authenticate(user=lecturer_user)

    url = "/api/users/register/student"
    data = {
        "first_name": "Jake",
        "last_name": "Student",
        "email": "jake.student@example.com",
        "student_id": "BCS/000003",
        "program_id": program.program_id,
        "stream_id": stream.stream_id,
        "year_of_study": 2,
    }

    response = api_client.post(url, data, format="json")
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
"""Tests for Registration API endpoints."""
import pytest
from rest_framework import status
from django.urls import reverse

from user_management.infrastructure.orm.django_models import (
    User as UserModel,
    StudentProfile as StudentProfileModel,
    LecturerProfile as LecturerProfileModel,
)

pytestmark = pytest.mark.django_db


class TestRegisterLecturer:
    """Tests for POST /api/users/register/lecturer/"""
    
    def test_register_lecturer_success(self, api_client):
        url = reverse('user_management:register-lecturer')
        data = {
            'email': 'new.lecturer@example.com',
            'password': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'Lecturer',
            'department_name': 'Mathematics',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'access_token' in response.data
        assert 'refresh_token' in response.data
        assert response.data['email'] == 'new.lecturer@example.com'
        assert response.data['role'] == 'Lecturer'
        
        # Verify user created in DB
        user = UserModel.objects.get(email='new.lecturer@example.com')
        assert user.role == UserModel.Roles.LECTURER
        assert user.has_usable_password()
        
        # Verify lecturer profile created
        assert LecturerProfileModel.objects.filter(user=user).exists()
    
    def test_register_lecturer_duplicate_email(self, api_client, lecturer_user):
        url = reverse('user_management:register-lecturer')
        data = {
            'email': 'lecturer@example.com',  # Already exists
            'password': 'SecurePass123!',
            'first_name': 'Duplicate',
            'last_name': 'User',
            'department_name': 'Physics',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_409_CONFLICT
        assert 'email' in response.data or 'detail' in response.data or 'error' in response.data
    
    def test_register_lecturer_weak_password(self, api_client):
        url = reverse('user_management:register-lecturer')
        data = {
            'email': 'weak@example.com',
            'password': 'weak',  # Too weak
            'first_name': 'Weak',
            'last_name': 'Pass',
            'department_name': 'Chemistry',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_lecturer_invalid_email(self, api_client):
        url = reverse('user_management:register-lecturer')
        data = {
            'email': 'not-an-email',
            'password': 'SecurePass123!',
            'first_name': 'Invalid',
            'last_name': 'Email',
            'department_name': 'Biology',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_lecturer_missing_fields(self, api_client):
        url = reverse('user_management:register-lecturer')
        data = {
            'email': 'incomplete@example.com',
            # Missing password, names, department
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_lecturer_email_normalized(self, api_client):
        url = reverse('user_management:register-lecturer')
        data = {
            'email': 'CAPS.Email@EXAMPLE.COM',
            'password': 'SecurePass123!',
            'first_name': 'Caps',
            'last_name': 'Email',
            'department_name': 'English',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == 'caps.email@example.com'


class TestRegisterStudent:
    """Tests for POST /api/users/register/student/"""
    
    def test_register_student_success(self, authenticated_admin_client, sample_program_no_streams):
        url = reverse('user_management:register-student')
        data = {
            'email': 'new.student@example.com',
            'first_name': 'New',
            'last_name': 'Student',
            'student_id': 'BBA/654321',
            'program_id': sample_program_no_streams.program_id,
            'year_of_study': 1,
        }
        
        response = authenticated_admin_client.post(url, data, format='json')
        
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == 'new.student@example.com'
        assert response.data['role'] == 'Student'
        
        # Verify student created
        user = UserModel.objects.get(email='new.student@example.com')
        assert user.role == UserModel.Roles.STUDENT
        assert not user.has_usable_password()
        
        # Verify student profile
        profile = StudentProfileModel.objects.get(user=user)
        assert profile.student_id == 'BBA/654321'
        assert profile.year_of_study == 1
    
    def test_register_student_with_stream(self, authenticated_admin_client, sample_program, sample_stream):
        url = reverse('user_management:register-student')
        data = {
            'email': 'stream.student@example.com',
            'first_name': 'Stream',
            'last_name': 'Student',
            'student_id': 'BCS/111111',
            'program_id': sample_program.program_id,
            'stream_id': sample_stream.stream_id,
            'year_of_study': 2,
        }
        
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        profile = StudentProfileModel.objects.get(student_id='BCS/111111')
        assert profile.stream_id == sample_stream.stream_id
    
    def test_register_student_non_admin_forbidden(self, authenticated_lecturer_client, sample_program):
        url = reverse('user_management:register-student')
        data = {
            'email': 'forbidden@example.com',
            'first_name': 'Forbidden',
            'last_name': 'Student',
            'student_id': 'BCS/999999',
            'program_id': sample_program.program_id,
            'year_of_study': 1,
        }
        
        response = authenticated_lecturer_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_register_student_unauthenticated(self, api_client, sample_program):
        url = reverse('user_management:register-student')
        data = {
            'email': 'noauth@example.com',
            'first_name': 'No',
            'last_name': 'Auth',
            'student_id': 'BCS/888888',
            'program_id': sample_program.program_id,
            'year_of_study': 1,
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_register_student_duplicate_email(self, authenticated_admin_client, student_user, sample_program):
        url = reverse('user_management:register-student')
        data = {
            'email': 'student@example.com',  # Already exists
            'first_name': 'Duplicate',
            'last_name': 'Student',
            'student_id': 'BCS/777777',
            'program_id': sample_program.program_id,
            'year_of_study': 1,
        }
        
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_409_CONFLICT
    
    def test_register_student_duplicate_student_id(self, authenticated_admin_client, student_user, sample_program):
        url = reverse('user_management:register-student')
        data = {
            'email': 'different@example.com',
            'first_name': 'Different',
            'last_name': 'Email',
            'student_id': 'BCS/123456',  # Already exists
            'program_id': sample_program.program_id,
            'year_of_study': 1,
        }
        
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_409_CONFLICT
    
    def test_register_student_invalid_student_id_format(self, authenticated_admin_client, sample_program):
        url = reverse('user_management:register-student')
        data = {
            'email': 'invalid.id@example.com',
            'first_name': 'Invalid',
            'last_name': 'ID',
            'student_id': 'INVALID123',  # Wrong format
            'program_id': sample_program.program_id,
            'year_of_study': 1,
        }
        
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_student_program_not_found(self, authenticated_admin_client):
        url = reverse('user_management:register-student')
        data = {
            'email': 'noprog@example.com',
            'first_name': 'No',
            'last_name': 'Program',
            'student_id': 'BCS/666666',
            'program_id': 99999,  # Doesn't exist
            'year_of_study': 1,
        }
        
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_register_student_invalid_year(self, authenticated_admin_client, sample_program):
        url = reverse('user_management:register-student')
        data = {
            'email': 'badyear@example.com',
            'first_name': 'Bad',
            'last_name': 'Year',
            'student_id': 'BCS/555555',
            'program_id': sample_program.program_id,
            'year_of_study': 5,  # Invalid (must be 1-4)
        }
        
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_student_stream_required_when_program_has_streams(
        self, authenticated_admin_client, sample_program
    ):
        """If program.has_streams=True and year >= stream start year, stream is required."""
        url = reverse('user_management:register-student')
        data = {
            'email': 'needstream@example.com',
            'first_name': 'Need',
            'last_name': 'Stream',
            'student_id': 'BCS/444444',
            'program_id': sample_program.program_id,
            'year_of_study': 2,  # Stream required
            # stream_id missing
        }
        
        response = authenticated_admin_client.post(url, data, format='json')
        
        # Should fail with StreamRequiredError (400)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_student_stream_not_allowed_when_program_no_streams(
        self, authenticated_admin_client, sample_program_no_streams, sample_stream
    ):
        url = reverse('user_management:register-student')
        data = {
            'email': 'nostream@example.com',
            'first_name': 'No',
            'last_name': 'Stream',
            'student_id': 'BBA/123456',
            'program_id': sample_program_no_streams.program_id,
            'stream_id': sample_stream.stream_id,  # Should not be allowed
            'year_of_study': 1,
        }
        
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_student_id_normalized_uppercase(self, authenticated_admin_client, sample_program_no_streams):
        """Test that lowercase student IDs are REJECTED (uppercase only per docs)."""
        url = reverse('user_management:register-student')
        data = {
            'email': 'normalize@example.com',
            'first_name': 'Norm',
            'last_name': 'Student',
            'student_id': 'bba/333333',  # lowercase - should be rejected
            'program_id': sample_program_no_streams.program_id,
            'year_of_study': 1,
        }
        
        response = authenticated_admin_client.post(url, data, format='json')
        
        # Should reject lowercase
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'student_id' in response.data
        assert 'uppercase' in str(response.data['student_id']).lower()


class TestRegisterAdmin:
    """Tests for POST /api/users/register/admin/"""
    
    def test_register_admin_success(self, authenticated_admin_client):
        url = reverse('user_management:register-admin')
        data = {
            'email': 'new.admin@example.com',
            'password': 'AdminPass123!',
            'first_name': 'New',
            'last_name': 'Admin',
        }
        
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        # Admin registration returns user data only, no tokens
        # New admin should login separately for security
        assert response.data['email'] == 'new.admin@example.com'
        assert response.data['role'] == 'Admin'
        assert response.data['user_id'] is not None
        assert response.data['is_active'] is True
        
        # Verify admin created
        user = UserModel.objects.get(email='new.admin@example.com')
        assert user.role == UserModel.Roles.ADMIN
        assert user.has_usable_password()
    
    def test_register_admin_non_admin_forbidden(self, authenticated_lecturer_client):
        url = reverse('user_management:register-admin')
        data = {
            'email': 'forbidden.admin@example.com',
            'password': 'AdminPass123!',
            'first_name': 'Forbidden',
            'last_name': 'Admin',
        }
        
        response = authenticated_lecturer_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_register_admin_unauthenticated(self, api_client):
        url = reverse('user_management:register-admin')
        data = {
            'email': 'noauth.admin@example.com',
            'password': 'AdminPass123!',
            'first_name': 'No',
            'last_name': 'Auth',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_register_admin_duplicate_email(self, authenticated_admin_client, admin_user):
        url = reverse('user_management:register-admin')
        data = {
            'email': 'admin@example.com',  # Already exists
            'password': 'AdminPass123!',
            'first_name': 'Duplicate',
            'last_name': 'Admin',
        }
        
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_409_CONFLICT
    
    def test_register_admin_weak_password(self, authenticated_admin_client):
        url = reverse('user_management:register-admin')
        data = {
            'email': 'weak.admin@example.com',
            'password': 'weak',
            'first_name': 'Weak',
            'last_name': 'Admin',
        }
        
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

