import pytest
from rest_framework import status


@pytest.mark.django_db
def test_is_owner_or_admin_blocks_other_user(api_client, student_user, lecturer_user, program, stream):
    # Create another student
    from user_management.infrastructure.orm.django_models import User, StudentProfile

    other = User.objects.create_user(
        email="other.student@example.com",
        role=User.Roles.STUDENT,
        first_name="Other",
        last_name="Student",
        password=None,
    )
    StudentProfile.objects.create(
        user=other,
        student_id="BCS/000010",
        program=program,
        stream=stream,
        year_of_study=2,
    )

    # Lecturer (not admin) tries to fetch other's profile
    api_client.force_authenticate(user=lecturer_user)
    url = f"/api/users/{other.user_id}/student-profile"
    response = api_client.get(url)
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@pytest.mark.django_db
def test_admin_can_access_other_profile(api_client, student_user, admin_user):
    api_client.force_authenticate(user=admin_user)
    url = f"/api/users/{student_user.user_id}/student-profile"
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
"""Tests for permission classes."""
import pytest
from rest_framework import status
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestIsAdminPermission:
    """Tests for IsAdmin permission class."""
    
    def test_admin_can_register_student(self, authenticated_admin_client, sample_program_no_streams):
        """Admin should be able to register students."""
        url = reverse('user_management:register-student')
        data = {
            'email': 'permission.test@example.com',
            'first_name': 'Permission',
            'last_name': 'Test',
            'student_id': 'BBA/999999',
            'program_id': sample_program_no_streams.program_id,
            'year_of_study': 1,
        }
        
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_lecturer_cannot_register_student(self, authenticated_lecturer_client, sample_program):
        """Lecturer should not be able to register students."""
        url = reverse('user_management:register-student')
        data = {
            'email': 'forbidden.test@example.com',
            'first_name': 'Forbidden',
            'last_name': 'Test',
            'student_id': 'BCS/888888',
            'program_id': sample_program.program_id,
            'year_of_study': 1,
        }
        
        response = authenticated_lecturer_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_unauthenticated_cannot_register_student(self, api_client, sample_program):
        """Unauthenticated requests should return 401."""
        url = reverse('user_management:register-student')
        data = {
            'email': 'unauth.test@example.com',
            'first_name': 'Unauth',
            'last_name': 'Test',
            'student_id': 'BCS/777777',
            'program_id': sample_program.program_id,
            'year_of_study': 1,
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestIsOwnerOrAdminPermission:
    """Tests for IsOwnerOrAdmin permission class."""
    
    def test_user_can_access_own_profile(self, authenticated_lecturer_client, lecturer_user):
        """User should be able to access their own profile."""
        url = reverse('user_management:user-detail', kwargs={'user_id': lecturer_user.user_id})
        
        response = authenticated_lecturer_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_user_cannot_access_other_profile(self, authenticated_lecturer_client, admin_user):
        """User should not be able to access another user's profile."""
        url = reverse('user_management:user-detail', kwargs={'user_id': admin_user.user_id})
        
        response = authenticated_lecturer_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_access_any_profile(self, authenticated_admin_client, lecturer_user):
        """Admin should be able to access any user's profile."""
        url = reverse('user_management:user-detail', kwargs={'user_id': lecturer_user.user_id})
        
        response = authenticated_admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK


class TestAuthenticationRequired:
    """Tests for authentication requirements."""
    
    def test_unauthenticated_cannot_access_user_detail(self, api_client, lecturer_user):
        """Unauthenticated requests to protected endpoints should return 401."""
        url = reverse('user_management:user-detail', kwargs={'user_id': lecturer_user.user_id})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_invalid_token_returns_401(self, api_client):
        """Invalid tokens should return 401."""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid.token.here')
        url = reverse('user_management:user-detail', kwargs={'user_id': 1})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_public_endpoints_accessible_without_auth(self, api_client):
        """Public endpoints like login should be accessible without authentication."""
        url = reverse('user_management:login')
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
        }
        
        response = api_client.post(url, data, format='json')
        
        # Should not be 401 (will be 401 for invalid credentials, but not for missing auth)
        # This endpoint should accept the request and validate credentials
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST]
        # Not 403 which would indicate auth required

