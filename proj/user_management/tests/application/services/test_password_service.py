import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
import jwt

from user_management.application.services.password_service import PasswordService
from user_management.domain.entities.user import User, UserRole
from user_management.domain.value_objects.email import Email
from user_management.domain.exceptions.core import (
    WeakPasswordError,
    InvalidPasswordError,
    StudentCannotHavePasswordError,
    InvalidTokenError,
    ExpiredTokenError,
    InvalidTokenTypeError,
)


# ---------------------
# Fixtures
# ---------------------

@pytest.fixture
def user_repository():
    return Mock()


@pytest.fixture
def service(user_repository):
    return PasswordService(user_repository=user_repository)


@pytest.fixture
def admin_user():
    return User(
        user_id=1,
        first_name="Alice",
        last_name="Admin",
        email=Email("alice.admin@example.com"),
        role=UserRole.ADMIN,
        is_active=True,
        has_password=True,
    )


@pytest.fixture
def lecturer_user():
    return User(
        user_id=2,
        first_name="Bob",
        last_name="Lecturer",
        email=Email("bob.lecturer@example.com"),
        role=UserRole.LECTURER,
        is_active=True,
        has_password=True,
    )


@pytest.fixture
def student_user():
    # Note: domain would disallow has_password for students, so set False
    return User(
        user_id=3,
        first_name="Charlie",
        last_name="Student",
        email=Email("charlie.student@example.com"),
        role=UserRole.STUDENT,
        is_active=True,
        has_password=False,
    )


# ---------------------
# A. Hash and Verify
# ---------------------

class TestHashAndVerify:
    def test_hash_and_verify_roundtrip(self, service):
        plain = "ValidPass123!"
        hashed = service.hash_password(plain)
        assert hashed and isinstance(hashed, str)
        assert hashed != plain
        assert service.verify_password(plain, hashed) is True
        assert service.verify_password("WrongPass!", hashed) is False

    def test_verify_returns_false_when_empty_hash(self, service):
        assert service.verify_password("anything", "") is False


# ---------------------
# B. Strength Validation
# ---------------------

class TestStrengthValidation:
    def test_too_short(self, service):
        with pytest.raises(WeakPasswordError):
            service.validate_password_strength("Aa1$abc")  # 7 chars

    def test_no_uppercase(self, service):
        with pytest.raises(WeakPasswordError):
            service.validate_password_strength("validpass123!")

    def test_no_lowercase(self, service):
        with pytest.raises(WeakPasswordError):
            service.validate_password_strength("VALIDPASS123!")

    def test_no_digit(self, service):
        with pytest.raises(WeakPasswordError):
            service.validate_password_strength("ValidPass!!!")

    def test_no_special(self, service):
        with pytest.raises(WeakPasswordError):
            service.validate_password_strength("ValidPass1234")

    def test_strong_password_passes(self, service):
        service.validate_password_strength("StrongPass123!")  # no exception


# ---------------------
# C. Change Password
# ---------------------

class TestChangePassword:
    def test_change_password_success(self, service, user_repository, lecturer_user):
        user_repository.get_by_id.return_value = lecturer_user
        old_hash = make_password("OldPass123!")
        mock_user_model = Mock()
        mock_user_model.password = old_hash

        with patch('user_management.infrastructure.orm.django_models.User') as MockUserModel:
            MockUserModel.objects.get.return_value = mock_user_model

            result = service.change_password(lecturer_user.user_id, "OldPass123!", "NewPass123!")

            # update_password called with a new hash that verifies
            assert user_repository.update_password.called is True
            call_args = user_repository.update_password.call_args[0]
            assert call_args[0] == lecturer_user.user_id
            new_hash = call_args[1]
            assert check_password("NewPass123!", new_hash) is True
            assert result == "Password changed successfully"

    def test_invalid_old_password_raises(self, service, user_repository, lecturer_user):
        user_repository.get_by_id.return_value = lecturer_user
        old_hash = make_password("OldPass123!")
        mock_user_model = Mock()
        mock_user_model.password = old_hash

        with patch('user_management.infrastructure.orm.django_models.User') as MockUserModel:
            MockUserModel.objects.get.return_value = mock_user_model

            with pytest.raises(InvalidPasswordError):
                service.change_password(lecturer_user.user_id, "WrongOld!", "NewPass123!")

            user_repository.update_password.assert_not_called()

    def test_new_password_same_as_old_raises(self, service, user_repository, lecturer_user):
        user_repository.get_by_id.return_value = lecturer_user
        old_hash = make_password("SamePass123!")
        mock_user_model = Mock()
        mock_user_model.password = old_hash

        with patch('user_management.infrastructure.orm.django_models.User') as MockUserModel:
            MockUserModel.objects.get.return_value = mock_user_model

            with pytest.raises(WeakPasswordError):
                service.change_password(lecturer_user.user_id, "SamePass123!", "SamePass123!")

            user_repository.update_password.assert_not_called()

    def test_student_cannot_change_password(self, service, user_repository, student_user):
        user_repository.get_by_id.return_value = student_user

        with pytest.raises(StudentCannotHavePasswordError):
            service.change_password(student_user.user_id, "OldPass123!", "NewPass123!")

        user_repository.update_password.assert_not_called()


# ---------------------
# D. Reset Token Generation
# ---------------------

class TestGenerateResetToken:
    def test_generate_reset_token_contains_claims(self, service, user_repository, admin_user):
        user_repository.get_by_id.return_value = admin_user
        before = datetime.now(tz=timezone.utc)
        token = service.generate_reset_token(admin_user.user_id)
        after = datetime.now(tz=timezone.utc)

        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        assert decoded['user_id'] == admin_user.user_id
        assert decoded['type'] == 'password_reset'
        # exp/iat boundaries
        iat_seconds = decoded['iat']
        exp = datetime.fromtimestamp(decoded['exp'], tz=timezone.utc)
        assert int(before.timestamp()) <= iat_seconds <= int(after.timestamp())
        iat_dt = datetime.fromtimestamp(iat_seconds, tz=timezone.utc)
        assert exp - iat_dt <= timedelta(minutes=service.reset_expiry_minutes) + timedelta(seconds=1)

    def test_student_cannot_get_reset_token(self, service, user_repository, student_user):
        user_repository.get_by_id.return_value = student_user
        with pytest.raises(StudentCannotHavePasswordError):
            service.generate_reset_token(student_user.user_id)


# ---------------------
# E. Reset Password
# ---------------------

class TestResetPassword:
    def test_reset_password_success(self, service, user_repository, admin_user):
        user_repository.get_by_id.return_value = admin_user
        # Generate a valid token first
        token = service.generate_reset_token(admin_user.user_id)

        # Perform reset
        result = service.reset_password(token, "BrandNew123!")

        # Ensure repository updated with a valid hash
        assert user_repository.update_password.called is True
        args = user_repository.update_password.call_args[0]
        assert args[0] == admin_user.user_id
        assert check_password("BrandNew123!", args[1]) is True
        assert result == "Password reset successfully"

    def test_reset_password_expired_token(self, service, user_repository, admin_user):
        user_repository.get_by_id.return_value = admin_user
        # Craft an already-expired token
        payload = {
            'user_id': admin_user.user_id,
            'type': 'password_reset',
            'iat': datetime.now(tz=timezone.utc) - timedelta(hours=2),
            'exp': datetime.now(tz=timezone.utc) - timedelta(hours=1),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        with pytest.raises(ExpiredTokenError):
            service.reset_password(token, "BrandNew123!")

        user_repository.update_password.assert_not_called()

    def test_reset_password_wrong_type(self, service, user_repository, admin_user):
        user_repository.get_by_id.return_value = admin_user
        # Create a token with wrong type
        payload = {
            'user_id': admin_user.user_id,
            'type': 'access',
            'iat': datetime.now(tz=timezone.utc),
            'exp': datetime.now(tz=timezone.utc) + timedelta(minutes=5),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        with pytest.raises(InvalidTokenTypeError):
            service.reset_password(token, "BrandNew123!")

        user_repository.update_password.assert_not_called()

    def test_reset_password_malformed_missing_user_id(self, service, user_repository, admin_user):
        user_repository.get_by_id.return_value = admin_user
        payload = {
            'type': 'password_reset',
            'iat': datetime.now(tz=timezone.utc),
            'exp': datetime.now(tz=timezone.utc) + timedelta(minutes=5),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        with pytest.raises(InvalidTokenError):
            service.reset_password(token, "BrandNew123!")

        user_repository.update_password.assert_not_called()
