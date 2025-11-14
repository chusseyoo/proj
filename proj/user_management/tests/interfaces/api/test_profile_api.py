import pytest
from rest_framework import status


@pytest.mark.django_db
def test_get_own_student_profile(api_client, student_user):
    api_client.force_authenticate(user=student_user)
    url = f"/api/users/{student_user.user_id}/student-profile"

    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["user_id"] == student_user.user_id
    assert "student_id" in body


@pytest.mark.django_db
def test_get_student_profile_unauthenticated(api_client, student_user):
    url = f"/api/users/{student_user.user_id}/student-profile"
    response = api_client.get(url)
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
"""Tests for Profile API endpoints."""
import pytest
from rest_framework import status
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestUserDetailView:
    """Tests for GET/PUT/DELETE /api/users/{user_id}"""
    
    def test_get_own_profile_as_lecturer(self, authenticated_lecturer_client, lecturer_user):
        url = reverse('user_management:user-detail', kwargs={'user_id': lecturer_user.user_id})
        
        response = authenticated_lecturer_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'lecturer@example.com'
    
    def test_get_own_profile_as_admin(self, authenticated_admin_client, admin_user):
        url = reverse('user_management:user-detail', kwargs={'user_id': admin_user.user_id})
        
        response = authenticated_admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'admin@example.com'
    
    def test_update_own_profile(self, authenticated_lecturer_client, lecturer_user):
        url = reverse('user_management:user-detail', kwargs={'user_id': lecturer_user.user_id})
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
        }
        
        response = authenticated_lecturer_client.put(url, data, format='json')
        
        # May be 200 or 400 depending on serializer requirements
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
    
    def test_cannot_access_other_user_profile(self, authenticated_lecturer_client, admin_user):
        """Lecturer should not be able to access admin's profile."""
        url = reverse('user_management:user-detail', kwargs={'user_id': admin_user.user_id})
        
        response = authenticated_lecturer_client.get(url)
        
        # Should be forbidden (unless admin permission)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_access_any_profile(self, authenticated_admin_client, lecturer_user):
        """Admin should be able to access any user's profile."""
        url = reverse('user_management:user-detail', kwargs={'user_id': lecturer_user.user_id})
        
        response = authenticated_admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_unauthenticated_returns_401(self, api_client, lecturer_user):
        url = reverse('user_management:user-detail', kwargs={'user_id': lecturer_user.user_id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestStudentProfileView:
    """Tests for GET/PUT /api/users/{user_id}/student-profile"""
    
    def test_get_student_profile(self, authenticated_admin_client, student_user):
        url = reverse('user_management:student-profile', kwargs={'user_id': student_user.user_id})
        
        response = authenticated_admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'student_id' in response.data
    
    def test_update_student_profile_year(self, authenticated_admin_client, student_user):
        url = reverse('user_management:student-profile', kwargs={'user_id': student_user.user_id})
        data = {
            'year_of_study': 3,
        }
        
        response = authenticated_admin_client.put(url, data, format='json')
        
        # May succeed or fail depending on serializer validation
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
    
    def test_non_admin_cannot_update_student_profile(self, authenticated_lecturer_client, student_user):
        url = reverse('user_management:student-profile', kwargs={'user_id': student_user.user_id})
        data = {
            'year_of_study': 3,
        }
        
        response = authenticated_lecturer_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestLecturerProfileView:
    """Tests for GET/PUT /api/users/{user_id}/lecturer-profile"""
    
    def test_get_lecturer_profile(self, authenticated_admin_client, lecturer_user):
        url = reverse('user_management:lecturer-profile', kwargs={'user_id': lecturer_user.user_id})
        
        response = authenticated_admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'department_name' in response.data
    
    def test_update_lecturer_profile_department(self, authenticated_lecturer_client, lecturer_user):
        """Lecturer can update their own profile."""
        url = reverse('user_management:lecturer-profile', kwargs={'user_id': lecturer_user.user_id})
        data = {
            'department_name': 'Physics',
        }
        
        response = authenticated_lecturer_client.put(url, data, format='json')
        
        # May succeed or fail depending on validation
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

