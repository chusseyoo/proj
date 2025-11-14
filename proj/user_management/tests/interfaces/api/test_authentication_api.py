import pytest
from rest_framework import status


@pytest.mark.django_db
def test_login_lecturer_success(api_client, lecturer_user):
    url = "/api/users/login"
    data = {"email": "lecturer@example.com", "password": "LecturerPass123!"}

    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "access_token" in body and "refresh_token" in body


@pytest.mark.django_db
def test_login_admin_success(api_client, admin_user):
    url = "/api/users/login"
    data = {"email": "admin@example.com", "password": "AdminPass123!"}

    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "access_token" in body and "refresh_token" in body
"""Tests for Authentication API endpoints."""
import pytest
from rest_framework import status
from django.urls import reverse
import jwt
import time

pytestmark = pytest.mark.django_db


class TestLogin:
    """Tests for POST /api/users/login"""
    
    def test_login_lecturer_success(self, api_client, lecturer_user):
        url = reverse('user_management:login')
        data = {
            'email': 'lecturer@example.com',
            'password': 'LecturerPass123!',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access_token' in response.data
        assert 'refresh_token' in response.data
        assert 'user' in response.data
        assert response.data['user']['email'] == 'lecturer@example.com'
        assert response.data['user']['role'] == 'Lecturer'
    
    def test_login_admin_success(self, api_client, admin_user):
        url = reverse('user_management:login')
        data = {
            'email': 'admin@example.com',
            'password': 'AdminPass123!',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access_token' in response.data
        assert 'refresh_token' in response.data
        assert response.data['user']['role'] == 'Admin'
    
    def test_login_returns_valid_tokens(self, api_client, lecturer_user):
        url = reverse('user_management:login')
        data = {
            'email': 'lecturer@example.com',
            'password': 'LecturerPass123!',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify access token structure (don't verify signature in test)
        access_token = response.data['access_token']
        access_payload = jwt.decode(access_token, options={"verify_signature": False})
        assert access_payload['type'] == 'access'
        assert 'user_id' in access_payload
        assert 'email' in access_payload
        assert 'exp' in access_payload
        
        # Verify refresh token structure
        refresh_token = response.data['refresh_token']
        refresh_payload = jwt.decode(refresh_token, options={"verify_signature": False})
        assert refresh_payload['type'] == 'refresh'
        assert 'user_id' in refresh_payload
        assert 'jti' in refresh_payload
    
    def test_login_email_case_insensitive(self, api_client, lecturer_user):
        url = reverse('user_management:login')
        data = {
            'email': 'LECTURER@EXAMPLE.COM',
            'password': 'LecturerPass123!',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_login_invalid_email_raises_invalid_credentials(self, api_client):
        url = reverse('user_management:login')
        data = {
            'email': 'nonexistent@example.com',
            'password': 'AnyPassword123!',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'detail' in response.data or 'error' in response.data
    
    def test_login_wrong_password_raises_invalid_credentials(self, api_client, lecturer_user):
        url = reverse('user_management:login')
        data = {
            'email': 'lecturer@example.com',
            'password': 'WrongPassword123!',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_student_raises_student_cannot_login(self, api_client, student_user):
        """Students cannot log in via standard login (they use attendance tokens)."""
        url = reverse('user_management:login')
        data = {
            'email': 'student@example.com',
            'password': 'anypassword',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_login_inactive_user_raises_user_inactive(self, api_client, lecturer_user):
        # Deactivate user
        lecturer_user.is_active = False
        lecturer_user.save()
        
        url = reverse('user_management:login')
        data = {
            'email': 'lecturer@example.com',
            'password': 'LecturerPass123!',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_login_email_with_spaces_trimmed(self, api_client, lecturer_user):
        url = reverse('user_management:login')
        data = {
            'email': '  lecturer@example.com  ',
            'password': 'LecturerPass123!',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_login_missing_email(self, api_client):
        url = reverse('user_management:login')
        data = {
            'password': 'SomePassword123!',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_login_missing_password(self, api_client):
        url = reverse('user_management:login')
        data = {
            'email': 'test@example.com',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestRefreshToken:
    """Tests for POST /api/users/refresh"""
    
    def test_refresh_token_success(self, api_client, lecturer_user):
        # First login to get tokens
        login_url = reverse('user_management:login')
        login_data = {
            'email': 'lecturer@example.com',
            'password': 'LecturerPass123!',
        }
        login_response = api_client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['refresh_token']
        
        # Now refresh
        refresh_url = reverse('user_management:refresh')
        refresh_data = {
            'refresh_token': refresh_token,
        }
        
        response = api_client.post(refresh_url, refresh_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access_token' in response.data
        # May also return new refresh token if rotation enabled
    
    def test_refresh_token_returns_new_access_token(self, api_client, lecturer_user):
        """New access token should have different jti from old one."""
        # Login
        login_url = reverse('user_management:login')
        login_data = {
            'email': 'lecturer@example.com',
            'password': 'LecturerPass123!',
        }
        login_response = api_client.post(login_url, login_data, format='json')
        old_access = login_response.data['access_token']
        refresh_token = login_response.data['refresh_token']
        
        # Refresh
        refresh_url = reverse('user_management:refresh')
        response = api_client.post(refresh_url, {'refresh_token': refresh_token}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        new_access = response.data['access_token']
        
        # Tokens should have different JTI (unique token IDs)
        old_payload = jwt.decode(old_access, options={"verify_signature": False})
        new_payload = jwt.decode(new_access, options={"verify_signature": False})
        
        assert 'jti' in old_payload
        assert 'jti' in new_payload
        assert old_payload['jti'] != new_payload['jti']  # Different unique IDs
        assert old_payload['user_id'] == new_payload['user_id']  # Same user
    
    def test_refresh_invalid_token_raises_error(self, api_client):
        url = reverse('user_management:refresh')
        data = {
            'refresh_token': 'invalid.token.here',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_expired_token_raises_error(self, api_client):
        """Test with a manually crafted expired token."""
        import jwt
        from datetime import datetime, timedelta, timezone
        
        # Create an expired token
        payload = {
            'user_id': 1,
            'type': 'refresh',
            'exp': datetime.now(timezone.utc) - timedelta(days=1),  # Expired yesterday
            'jti': 'test-jti',
        }
        expired_token = jwt.encode(payload, 'test-secret-key', algorithm='HS256')
        
        url = reverse('user_management:refresh')
        data = {
            'refresh_token': expired_token,
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_with_access_token_raises_type_error(self, api_client, lecturer_user):
        """Trying to refresh using an access token should fail."""
        # Login
        login_url = reverse('user_management:login')
        login_response = api_client.post(
            login_url,
            {'email': 'lecturer@example.com', 'password': 'LecturerPass123!'},
            format='json'
        )
        access_token = login_response.data['access_token']
        
        # Try to use access token for refresh
        url = reverse('user_management:refresh')
        data = {
            'refresh_token': access_token,  # Wrong type!
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_missing_token(self, api_client):
        url = reverse('user_management:refresh')
        data = {}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_refresh_inactive_user_raises_error(self, api_client, lecturer_user):
        # Login first
        login_url = reverse('user_management:login')
        login_response = api_client.post(
            login_url,
            {'email': 'lecturer@example.com', 'password': 'LecturerPass123!'},
            format='json'
        )
        refresh_token = login_response.data['refresh_token']
        
        # Deactivate user
        lecturer_user.is_active = False
        lecturer_user.save()
        
        # Try to refresh
        url = reverse('user_management:refresh')
        response = api_client.post(url, {'refresh_token': refresh_token}, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestTokenValidation:
    """Tests for token validation (used by authentication middleware)."""
    
    def test_access_token_allows_authenticated_request(self, authenticated_lecturer_client):
        """An authenticated request with valid access token should work."""
        # Try to access a protected endpoint (e.g., user detail)
        # This tests that the token middleware accepts the token
        url = reverse('user_management:user-detail', kwargs={'user_id': 1})
        
        response = authenticated_lecturer_client.get(url)
        
        # Should not be 401 (may be 403/404 depending on permissions, but authenticated)
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
    
    def test_invalid_token_returns_401(self, api_client):
        """Request with invalid token should return 401."""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid.token.here')
        
        url = reverse('user_management:user-detail', kwargs={'user_id': 1})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_missing_token_returns_401(self, api_client, lecturer_user):
        """Request without token to protected endpoint should return 401."""
        url = reverse('user_management:user-detail', kwargs={'user_id': lecturer_user.user_id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_expired_access_token_returns_401(self, api_client, lecturer_user):
        """Expired access token should return 401."""
        import jwt
        from datetime import datetime, timedelta, timezone
        payload = {
            'user_id': lecturer_user.user_id,
            'email': 'test@example.com',
            'role': 'Lecturer',
            'type': 'access',
            'exp': datetime.now(timezone.utc) - timedelta(minutes=1),  # Expired
            'iat': datetime.now(timezone.utc) - timedelta(minutes=20),
        }
        from django.conf import settings
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        url = reverse('user_management:user-detail', kwargs={'user_id': lecturer_user.user_id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

