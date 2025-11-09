import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone
import jwt
from django.conf import settings

from user_management.application.services.authentication_service import AuthenticationService
from user_management.domain.entities import User, UserRole
from user_management.domain.value_objects import Email
from user_management.domain.exceptions import (
    InvalidCredentialsError,
    StudentCannotLoginError,
    UserInactiveError,
    InvalidTokenError,
    ExpiredTokenError,
    InvalidTokenTypeError,
)
from user_management.application.ports import RefreshTokenRecord


# ===========================
# Fixtures
# ===========================

@pytest.fixture()
def user_repository():
    """Mock UserRepository."""
    return Mock()


@pytest.fixture()
def password_service():
    """Mock PasswordService."""
    svc = Mock()
    svc.verify_password.return_value = True
    return svc


@pytest.fixture()
def student_repository():
    """Mock StudentProfileRepository."""
    return Mock()


@pytest.fixture()
def refresh_store():
    """Mock RefreshTokenStorePort."""
    store = Mock()
    store.is_revoked.return_value = False
    return store


@pytest.fixture()
def service(user_repository, password_service, student_repository):
    """AuthenticationService without refresh store (stateless)."""
    return AuthenticationService(
        user_repository=user_repository,
        password_service=password_service,
        student_repository=student_repository,
        refresh_store=None,
    )


@pytest.fixture()
def service_with_store(user_repository, password_service, student_repository, refresh_store):
    """AuthenticationService with refresh store configured."""
    return AuthenticationService(
        user_repository=user_repository,
        password_service=password_service,
        student_repository=student_repository,
        refresh_store=refresh_store,
    )


@pytest.fixture()
def lecturer_user():
    """Mock lecturer user."""
    return User(
        user_id=1,
        first_name='John',
        last_name='Doe',
        email=Email('john.doe@example.com'),
        role=UserRole.LECTURER,
        is_active=True,
        has_password=True,
    )


@pytest.fixture()
def admin_user():
    """Mock admin user."""
    return User(
        user_id=2,
        first_name='Admin',
        last_name='User',
        email=Email('admin@example.com'),
        role=UserRole.ADMIN,
        is_active=True,
        has_password=True,
    )


@pytest.fixture()
def student_user():
    """Mock student user."""
    return User(
        user_id=3,
        first_name='Jane',
        last_name='Student',
        email=Email('jane.student@example.com'),
        role=UserRole.STUDENT,
        is_active=True,
        has_password=False,
    )


@pytest.fixture()
def inactive_user():
    """Mock inactive lecturer user."""
    return User(
        user_id=4,
        first_name='Inactive',
        last_name='User',
        email=Email('inactive@example.com'),
        role=UserRole.LECTURER,
        is_active=False,
        has_password=True,
    )


@pytest.fixture()
def mock_user_model():
    """Mock Django UserModel."""
    model = Mock()
    model.user_id = 1
    model.password = 'hashed_password_from_db'
    return model


# ===========================
# Test Login
# ===========================

class TestLogin:
    """Test suite for login functionality."""
    
    # ---------------------
    # A. Success Path
    # ---------------------
    
    def test_login_lecturer_success(
        self, service, user_repository, password_service, lecturer_user, mock_user_model
    ):
        """Test successful lecturer login."""
        user_repository.find_by_email.return_value = lecturer_user
        
        with patch('user_management.infrastructure.orm.django_models.User') as MockUserModel:
            MockUserModel.objects.get.return_value = mock_user_model
            
            result = service.login('john.doe@example.com', 'ValidPass123!')
        
        # Assertions
        assert 'access_token' in result
        assert 'refresh_token' in result
        assert 'user' in result
        
        user_data = result['user']
        assert user_data['user_id'] == 1
        assert user_data['email'] == 'john.doe@example.com'
        assert user_data['role'] == 'Lecturer'
        assert user_data['full_name'] == 'John Doe'
        
        # Verify interactions
        user_repository.find_by_email.assert_called_once_with('john.doe@example.com')
        password_service.verify_password.assert_called_once_with('ValidPass123!', 'hashed_password_from_db')
    
    def test_login_admin_success(
        self, service, user_repository, password_service, admin_user, mock_user_model
    ):
        """Test successful admin login."""
        user_repository.find_by_email.return_value = admin_user
        mock_user_model.user_id = 2
        
        with patch('user_management.infrastructure.orm.django_models.User') as MockUserModel:
            MockUserModel.objects.get.return_value = mock_user_model
            
            result = service.login('admin@example.com', 'AdminPass123!')
        
        assert result['user']['role'] == 'Admin'
        assert result['user']['user_id'] == 2
    
    def test_returns_access_and_refresh_tokens(
        self, service, user_repository, lecturer_user, mock_user_model
    ):
        """Test that login returns both access and refresh tokens."""
        user_repository.find_by_email.return_value = lecturer_user
        
        with patch('user_management.infrastructure.orm.django_models.User') as MockUserModel:
            MockUserModel.objects.get.return_value = mock_user_model
            
            result = service.login('john.doe@example.com', 'ValidPass123!')
        
        # Verify token structure (basic validation)
        access_token = result['access_token']
        refresh_token = result['refresh_token']
        
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        assert len(access_token) > 20
        assert len(refresh_token) > 20
        assert access_token != refresh_token
    
    def test_returns_user_info(
        self, service, user_repository, lecturer_user, mock_user_model
    ):
        """Test that login returns complete user information."""
        user_repository.find_by_email.return_value = lecturer_user
        
        with patch('user_management.infrastructure.orm.django_models.User') as MockUserModel:
            MockUserModel.objects.get.return_value = mock_user_model
            
            result = service.login('john.doe@example.com', 'ValidPass123!')
        
        user_data = result['user']
        assert 'user_id' in user_data
        assert 'email' in user_data
        assert 'role' in user_data
        assert 'full_name' in user_data
    
    def test_email_case_insensitive(
        self, service, user_repository, lecturer_user, mock_user_model
    ):
        """Test that email is case-insensitive during login."""
        user_repository.find_by_email.return_value = lecturer_user
        
        with patch('user_management.infrastructure.orm.django_models.User') as MockUserModel:
            MockUserModel.objects.get.return_value = mock_user_model
            
            result = service.login('JOHN.DOE@EXAMPLE.COM', 'ValidPass123!')
        
        # Email should be normalized to lowercase
        user_repository.find_by_email.assert_called_once_with('john.doe@example.com')
        assert result['user']['email'] == 'john.doe@example.com'
    
    # ---------------------
    # B. Authentication Failures
    # ---------------------
    
    def test_invalid_email_raises_invalid_credentials(
        self, service, user_repository
    ):
        """Test that invalid email raises InvalidCredentialsError."""
        user_repository.find_by_email.return_value = None
        
        with pytest.raises(InvalidCredentialsError) as exc_info:
            service.login('nonexistent@example.com', 'AnyPassword123!')
        
        assert 'credentials' in str(exc_info.value).lower()
    
    def test_invalid_password_raises_invalid_credentials(
        self, service, user_repository, password_service, lecturer_user, mock_user_model
    ):
        """Test that invalid password raises InvalidCredentialsError."""
        user_repository.find_by_email.return_value = lecturer_user
        password_service.verify_password.return_value = False
        
        with patch('user_management.infrastructure.orm.django_models.User') as MockUserModel:
            MockUserModel.objects.get.return_value = mock_user_model
            
            with pytest.raises(InvalidCredentialsError):
                service.login('john.doe@example.com', 'WrongPassword!')
    
    def test_student_login_raises_student_cannot_login(
        self, service, user_repository, student_user, mock_user_model
    ):
        """Test that students cannot login with password."""
        user_repository.find_by_email.return_value = student_user
        mock_user_model.user_id = 3
        
        with patch('user_management.infrastructure.orm.django_models.User') as MockUserModel:
            MockUserModel.objects.get.return_value = mock_user_model
            
            with pytest.raises(StudentCannotLoginError) as exc_info:
                service.login('jane.student@example.com', 'AnyPassword123!')
            
            assert 'student' in str(exc_info.value).lower()
    
    def test_inactive_user_raises_user_inactive(
        self, service, user_repository, password_service, inactive_user, mock_user_model
    ):
        """Test that inactive users cannot login."""
        user_repository.find_by_email.return_value = inactive_user
        mock_user_model.user_id = 4
        
        with patch('user_management.infrastructure.orm.django_models.User') as MockUserModel:
            MockUserModel.objects.get.return_value = mock_user_model
            
            with pytest.raises(UserInactiveError) as exc_info:
                service.login('inactive@example.com', 'ValidPass123!')
            
            # Message wording may vary; assert the core meaning
            assert 'inactive' in str(exc_info.value).lower()
    
    # ---------------------
    # C. Edge Cases
    # ---------------------
    
    def test_email_with_spaces_trimmed(
        self, service, user_repository, lecturer_user, mock_user_model
    ):
        """Test that email with leading/trailing spaces is trimmed."""
        user_repository.find_by_email.return_value = lecturer_user
        
        with patch('user_management.infrastructure.orm.django_models.User') as MockUserModel:
            MockUserModel.objects.get.return_value = mock_user_model
            
            result = service.login('  john.doe@example.com  ', 'ValidPass123!')
        
        user_repository.find_by_email.assert_called_once_with('john.doe@example.com')
        assert result is not None
    
    def test_email_normalized_lowercase(
        self, service, user_repository, lecturer_user, mock_user_model
    ):
        """Test that email is normalized to lowercase."""
        user_repository.find_by_email.return_value = lecturer_user
        
        with patch('user_management.infrastructure.orm.django_models.User') as MockUserModel:
            MockUserModel.objects.get.return_value = mock_user_model
            
            service.login('John.Doe@EXAMPLE.COM', 'ValidPass123!')
        
        user_repository.find_by_email.assert_called_once_with('john.doe@example.com')
    
    # ---------------------
    # D. Integration
    # ---------------------
    
    def test_calls_password_service_verify(
        self, service, user_repository, password_service, lecturer_user, mock_user_model
    ):
        """Test that password verification is called correctly."""
        user_repository.find_by_email.return_value = lecturer_user
        
        with patch('user_management.infrastructure.orm.django_models.User') as MockUserModel:
            MockUserModel.objects.get.return_value = mock_user_model
            
            service.login('john.doe@example.com', 'TestPassword123!')
        
        password_service.verify_password.assert_called_once_with(
            'TestPassword123!', 
            'hashed_password_from_db'
        )
    
    def test_fetches_password_hash_from_orm(
        self, service, user_repository, lecturer_user, mock_user_model
    ):
        """Test that password hash is fetched from ORM."""
        user_repository.find_by_email.return_value = lecturer_user
        
        with patch('user_management.infrastructure.orm.django_models.User') as MockUserModel:
            MockUserModel.objects.get.return_value = mock_user_model
            
            service.login('john.doe@example.com', 'ValidPass123!')
        
        MockUserModel.objects.get.assert_called_once_with(user_id=1)


# ===========================
# Test Token Generation
# ===========================

class TestTokenGeneration:
    """Test suite for token generation."""
    
    # ---------------------
    # A. Access Token
    # ---------------------
    
    def test_generate_access_token_contains_user_info(
        self, service, lecturer_user
    ):
        """Test that access token contains user information."""
        token = service.generate_access_token(lecturer_user)
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        
        assert decoded['user_id'] == 1
        assert decoded['email'] == 'john.doe@example.com'
        assert decoded['role'] == 'Lecturer'
        assert decoded['type'] == 'access'
    
    def test_access_token_expires_in_15_minutes(
        self, service, lecturer_user
    ):
        """Test that access token expires in 15 minutes."""
        before = datetime.now(tz=timezone.utc)
        token = service.generate_access_token(lecturer_user)
        after = datetime.now(tz=timezone.utc)
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        exp = datetime.fromtimestamp(decoded['exp'], tz=timezone.utc)
        
        # Should expire between 14.5 and 15.5 minutes from now
        expected_min = before + timedelta(minutes=14, seconds=30)
        expected_max = after + timedelta(minutes=15, seconds=30)
        
        assert expected_min <= exp <= expected_max
    
    def test_access_token_type_is_access(
        self, service, lecturer_user
    ):
        """Test that access token has type 'access'."""
        token = service.generate_access_token(lecturer_user)
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        
        assert decoded['type'] == 'access'
    
    def test_access_token_has_iat(
        self, service, lecturer_user
    ):
        """Test that access token has issued-at timestamp."""
        before = datetime.now(tz=timezone.utc)
        token = service.generate_access_token(lecturer_user)
        after = datetime.now(tz=timezone.utc)
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        # PyJWT stores iat as integer seconds (Unix epoch). Our before/after include microseconds
        # which can make before slightly later within the same second and fail the comparison.
        # Compare using second precision to avoid false negatives.
        iat_seconds = decoded['iat']  # already an int
        assert int(before.timestamp()) <= iat_seconds <= int(after.timestamp())
    
    # ---------------------
    # B. Refresh Token
    # ---------------------
    
    def test_generate_refresh_token_contains_user_id_only(
        self, service, lecturer_user
    ):
        """Test that refresh token contains minimal user info (user_id only)."""
        token = service.generate_refresh_token(lecturer_user)
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        
        assert decoded['user_id'] == 1
        assert 'email' not in decoded  # Security: minimal info in refresh token
        assert 'role' not in decoded
        assert decoded['type'] == 'refresh'
    
    def test_refresh_token_expires_in_7_days(
        self, service, lecturer_user
    ):
        """Test that refresh token expires in 7 days."""
        before = datetime.now(tz=timezone.utc)
        token = service.generate_refresh_token(lecturer_user)
        after = datetime.now(tz=timezone.utc)
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        exp = datetime.fromtimestamp(decoded['exp'], tz=timezone.utc)
        
        # Should expire between 6.99 and 7.01 days from now
        expected_min = before + timedelta(days=6, hours=23)
        expected_max = after + timedelta(days=7, hours=1)
        
        assert expected_min <= exp <= expected_max
    
    def test_refresh_token_type_is_refresh(
        self, service, lecturer_user
    ):
        """Test that refresh token has type 'refresh'."""
        token = service.generate_refresh_token(lecturer_user)
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        
        assert decoded['type'] == 'refresh'
    
    def test_refresh_token_has_jti(
        self, service, lecturer_user
    ):
        """Test that refresh token has unique identifier (jti)."""
        token = service.generate_refresh_token(lecturer_user)
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        
        assert 'jti' in decoded
        assert isinstance(decoded['jti'], str)
        assert len(decoded['jti']) > 0
    
    # ---------------------
    # C. Refresh Token Store
    # ---------------------
    
    def test_saves_refresh_token_to_store_if_configured(
        self, service_with_store, refresh_store, lecturer_user
    ):
        """Test that refresh token is saved to store if configured."""
        token = service_with_store.generate_refresh_token(lecturer_user)
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        jti = decoded['jti']
        
        # Verify store.save was called
        refresh_store.save.assert_called_once()
        
        # Verify the record passed to save
        call_args = refresh_store.save.call_args[0][0]
        assert call_args.jti == jti
        assert call_args.user_id == 1
    
    def test_works_without_store_stateless(
        self, service, lecturer_user
    ):
        """Test that token generation works without store (stateless mode)."""
        # service fixture has refresh_store=None
        token = service.generate_refresh_token(lecturer_user)
        
        assert token is not None
        assert isinstance(token, str)
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        assert decoded['user_id'] == 1


# ===========================
# Test Token Validation
# ===========================

class TestTokenValidation:
    """Test suite for token validation."""
    
    # ---------------------
    # A. Valid Tokens
    # ---------------------
    
    def test_validate_valid_access_token(
        self, service, lecturer_user
    ):
        """Test validation of a valid access token."""
        token = service.generate_access_token(lecturer_user)
        
        decoded = service.validate_token(token, token_type='access')
        
        assert decoded['user_id'] == 1
        assert decoded['type'] == 'access'
    
    def test_validate_valid_refresh_token(
        self, service, lecturer_user
    ):
        """Test validation of a valid refresh token."""
        token = service.generate_refresh_token(lecturer_user)
        
        decoded = service.validate_token(token, token_type='refresh')
        
        assert decoded['user_id'] == 1
        assert decoded['type'] == 'refresh'
    
    # ---------------------
    # B. Invalid Tokens
    # ---------------------
    
    def test_expired_token_raises_expired_error(
        self, service, lecturer_user
    ):
        """Test that expired token raises ExpiredTokenError."""
        # Create token that expires immediately
        service.access_minutes = -1  # Negative = already expired
        token = service.generate_access_token(lecturer_user)
        service.access_minutes = 15  # Reset
        
        with pytest.raises(ExpiredTokenError) as exc_info:
            service.validate_token(token, token_type='access')
        
        assert 'expired' in str(exc_info.value).lower()
    
    def test_malformed_token_raises_invalid_error(
        self, service
    ):
        """Test that malformed token raises InvalidTokenError."""
        with pytest.raises(InvalidTokenError):
            service.validate_token('not.a.valid.token', token_type='access')
    
    def test_wrong_token_type_raises_type_error(
        self, service, lecturer_user
    ):
        """Test that wrong token type raises InvalidTokenTypeError."""
        access_token = service.generate_access_token(lecturer_user)
        
        with pytest.raises(InvalidTokenTypeError):
            service.validate_token(access_token, token_type='refresh')
    
    def test_tampered_signature_raises_invalid_error(
        self, service, lecturer_user
    ):
        """Test that tampered token signature raises InvalidTokenError."""
        token = service.generate_access_token(lecturer_user)
        
        # Tamper the signature segment deterministically
        header, payload, signature = token.split('.')
        tampered_token = f"{header}.{payload}.AAAA"
        
        with pytest.raises(InvalidTokenError):
            service.validate_token(tampered_token, token_type='access')
    
    # ---------------------
    # C. Edge Cases
    # ---------------------
    
    def test_token_without_exp_raises_error(
        self, service
    ):
        """Test that token without expiration raises error."""
        # Manually create token without exp
        payload = {'user_id': 1, 'type': 'access'}
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        
        with pytest.raises((InvalidTokenError, jwt.DecodeError)):
            service.validate_token(token, token_type='access')
    
    def test_token_without_type_raises_error(
        self, service, lecturer_user
    ):
        """Test that token without type field raises error."""
        # Manually create token without type
        payload = {
            'user_id': 1,
            'exp': datetime.now(tz=timezone.utc) + timedelta(minutes=15),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        
        with pytest.raises(InvalidTokenTypeError):
            service.validate_token(token, token_type='access')


# ===========================
# Test Refresh Access Token
# ===========================

class TestRefreshAccessToken:
    """Test suite for refreshing access tokens."""
    
    # ---------------------
    # A. Success Path
    # ---------------------
    
    def test_refresh_returns_new_access_token(
        self, service, user_repository, lecturer_user
    ):
        """Test that refresh returns a new access token."""
        refresh_token = service.generate_refresh_token(lecturer_user)
        user_repository.get_by_id.return_value = lecturer_user
        
        result = service.refresh_access_token(refresh_token)
        
        assert 'access_token' in result
        assert isinstance(result['access_token'], str)
        
        # Verify it's a valid access token
        decoded = jwt.decode(result['access_token'], settings.SECRET_KEY, algorithms=['HS256'])
        assert decoded['type'] == 'access'
        assert decoded['user_id'] == 1
    
    def test_refresh_validates_refresh_token(
        self, service, user_repository, lecturer_user
    ):
        """Test that refresh validates the refresh token."""
        # Try with invalid token
        with pytest.raises(InvalidTokenError):
            service.refresh_access_token('invalid.token.here')
        
        # Try with access token (wrong type)
        access_token = service.generate_access_token(lecturer_user)
        with pytest.raises(InvalidTokenTypeError):
            service.refresh_access_token(access_token)
    
    def test_refresh_checks_user_active(
        self, service, user_repository, inactive_user
    ):
        """Test that refresh checks if user is still active."""
        refresh_token = service.generate_refresh_token(inactive_user)
        user_repository.get_by_id.return_value = inactive_user
        
        with pytest.raises(UserInactiveError):
            service.refresh_access_token(refresh_token)
    
    # ---------------------
    # B. With Refresh Store (rotation)
    # ---------------------
    
    def test_rotates_refresh_token_if_store_configured(
        self, service_with_store, refresh_store, user_repository, lecturer_user
    ):
        """Test that refresh token is rotated when store is configured."""
        refresh_token = service_with_store.generate_refresh_token(lecturer_user)
        user_repository.get_by_id.return_value = lecturer_user
        
        result = service_with_store.refresh_access_token(refresh_token)
        
        # Should return new refresh token
        assert 'refresh_token' in result
        assert result['refresh_token'] is not None
        assert result['refresh_token'] != refresh_token
        
        # Verify store.rotate was called
        refresh_store.rotate.assert_called_once()
    
    def test_revokes_old_token_on_rotation(
        self, service_with_store, refresh_store, user_repository, lecturer_user
    ):
        """Test that old refresh token is revoked on rotation."""
        old_token = service_with_store.generate_refresh_token(lecturer_user)
        user_repository.get_by_id.return_value = lecturer_user
        
        decoded = jwt.decode(old_token, settings.SECRET_KEY, algorithms=['HS256'])
        old_jti = decoded['jti']
        
        service_with_store.refresh_access_token(old_token)
        
        # Verify rotate was called with old jti
        call_args = refresh_store.rotate.call_args
        assert call_args[0][0] == old_jti  # First arg is old_jti
    
    def test_revoked_token_raises_error(
        self, service_with_store, refresh_store, user_repository, lecturer_user
    ):
        """Test that using a revoked token raises error."""
        refresh_token = service_with_store.generate_refresh_token(lecturer_user)
        user_repository.get_by_id.return_value = lecturer_user
        
        # Mark token as revoked
        refresh_store.is_revoked.return_value = True
        
        with pytest.raises(InvalidTokenError) as exc_info:
            service_with_store.refresh_access_token(refresh_token)
        
        assert 'revoked' in str(exc_info.value).lower()
    
    # ---------------------
    # C. Errors
    # ---------------------
    
    def test_invalid_refresh_token_raises_error(
        self, service, user_repository
    ):
        """Test that invalid refresh token raises error."""
        with pytest.raises(InvalidTokenError):
            service.refresh_access_token('completely.invalid.token')
    
    def test_expired_refresh_token_raises_error(
        self, service, user_repository, lecturer_user
    ):
        """Test that expired refresh token raises error."""
        service.refresh_days = -1  # Make it expire immediately
        refresh_token = service.generate_refresh_token(lecturer_user)
        service.refresh_days = 7  # Reset
        
        with pytest.raises(ExpiredTokenError):
            service.refresh_access_token(refresh_token)
    
    def test_inactive_user_raises_error(
        self, service, user_repository, inactive_user
    ):
        """Test that inactive user cannot refresh token."""
        refresh_token = service.generate_refresh_token(inactive_user)
        user_repository.get_by_id.return_value = inactive_user
        
        with pytest.raises(UserInactiveError):
            service.refresh_access_token(refresh_token)


# ===========================
# Test Revoke Refresh Token
# ===========================

class TestRevokeRefreshToken:
    """Test suite for revoking refresh tokens."""
    
    def test_revoke_calls_store_if_configured(
        self, service_with_store, refresh_store, lecturer_user
    ):
        """Test that revoke calls store if configured."""
        refresh_token = service_with_store.generate_refresh_token(lecturer_user)
        
        decoded = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
        jti = decoded['jti']
        
        service_with_store.revoke_refresh_token(refresh_token)
        
        refresh_store.revoke.assert_called_once_with(jti)
    
    def test_revoke_ignores_if_no_store(
        self, service, lecturer_user
    ):
        """Test that revoke does nothing if no store configured."""
        refresh_token = service.generate_refresh_token(lecturer_user)
        
        # Should not raise error, just do nothing
        service.revoke_refresh_token(refresh_token)
    
    def test_revoke_expired_token_succeeds(
        self, service_with_store, refresh_store, lecturer_user
    ):
        """Test that revoking expired token succeeds (no-op)."""
        service_with_store.refresh_days = -1
        refresh_token = service_with_store.generate_refresh_token(lecturer_user)
        service_with_store.refresh_days = 7
        
        # Should not raise error for expired token
        service_with_store.revoke_refresh_token(refresh_token)
        
        # Store should not be called for expired tokens
        refresh_store.revoke.assert_not_called()
    
    def test_revoke_invalid_token_succeeds(
        self, service_with_store, refresh_store
    ):
        """Test that revoking invalid token succeeds (no-op)."""
        # Should not raise error for invalid token
        service_with_store.revoke_refresh_token('invalid.token.here')
        
        # Store should not be called for invalid tokens
        refresh_store.revoke.assert_not_called()


# ===========================
# Test Student Attendance Token
# ===========================

class TestGenerateStudentAttendanceToken:
    """Test suite for generating student attendance tokens."""
    
    # ---------------------
    # A. Success Path
    # ---------------------
    
    def test_generates_attendance_token(
        self, service, student_repository
    ):
        """Test successful generation of attendance token."""
        from user_management.domain.entities import StudentProfile
        from user_management.domain.value_objects import StudentId
        
        student_profile = StudentProfile(
            student_profile_id=100,
            student_id=StudentId('BCS/123456'),
            user_id=3,
            program_id=1,
            stream_id=10,
            year_of_study=2,
            qr_code_data='BCS/123456',
        )
        student_repository.get_by_id.return_value = student_profile
        
        token = service.generate_student_attendance_token(100, 500)
        
        assert token is not None
        assert isinstance(token, str)
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        assert decoded['type'] == 'attendance'
    
    def test_token_contains_student_and_session_ids(
        self, service, student_repository
    ):
        """Test that attendance token contains student and session IDs."""
        from user_management.domain.entities import StudentProfile
        from user_management.domain.value_objects import StudentId
        
        student_profile = StudentProfile(
            student_profile_id=100,
            student_id=StudentId('BCS/123456'),
            user_id=3,
            program_id=1,
            stream_id=10,
            year_of_study=2,
            qr_code_data='BCS/123456',
        )
        student_repository.get_by_id.return_value = student_profile
        
        token = service.generate_student_attendance_token(100, 500)
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        assert decoded['student_profile_id'] == 100
        assert decoded['session_id'] == 500
    
    def test_token_expires_in_2_hours(
        self, service, student_repository
    ):
        """Test that attendance token expires in 2 hours."""
        from user_management.domain.entities import StudentProfile
        from user_management.domain.value_objects import StudentId
        
        student_profile = StudentProfile(
            student_profile_id=100,
            student_id=StudentId('BCS/123456'),
            user_id=3,
            program_id=1,
            stream_id=10,
            year_of_study=2,
            qr_code_data='BCS/123456',
        )
        student_repository.get_by_id.return_value = student_profile
        
        before = datetime.now(tz=timezone.utc)
        token = service.generate_student_attendance_token(100, 500)
        after = datetime.now(tz=timezone.utc)
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        exp = datetime.fromtimestamp(decoded['exp'], tz=timezone.utc)
        
        # Should expire between 1.99 and 2.01 hours from now
        expected_min = before + timedelta(hours=1, minutes=59)
        expected_max = after + timedelta(hours=2, minutes=1)
        
        assert expected_min <= exp <= expected_max
    
    def test_token_type_is_attendance(
        self, service, student_repository
    ):
        """Test that token type is 'attendance'."""
        from user_management.domain.entities import StudentProfile
        from user_management.domain.value_objects import StudentId
        
        student_profile = StudentProfile(
            student_profile_id=100,
            student_id=StudentId('BCS/123456'),
            user_id=3,
            program_id=1,
            stream_id=10,
            year_of_study=2,
            qr_code_data='BCS/123456',
        )
        student_repository.get_by_id.return_value = student_profile
        
        token = service.generate_student_attendance_token(100, 500)
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        assert decoded['type'] == 'attendance'
    
    # ---------------------
    # B. Validation
    # ---------------------
    
    def test_student_not_found_raises_error(
        self, service, student_repository
    ):
        """Test that non-existent student raises error."""
        from user_management.domain.exceptions import StudentNotFoundError
        
        student_repository.get_by_id.side_effect = StudentNotFoundError('Student not found')
        
        with pytest.raises(StudentNotFoundError):
            service.generate_student_attendance_token(999, 500)
