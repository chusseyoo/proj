import pytest
from unittest.mock import Mock, patch
from django.contrib.auth.hashers import make_password, check_password

from user_management.application.services.change_password_service import ChangePasswordService
from user_management.application.services.password_service import PasswordService
from user_management.domain.entities.user import User, UserRole
from user_management.domain.value_objects.email import Email
from user_management.domain.exceptions.core import (
    InvalidPasswordError,
    WeakPasswordError,
    UserNotFoundError,
    StudentCannotHavePasswordError,
)


# ---------------------
# Fixtures
# ---------------------

@pytest.fixture
def user_repository():
    return Mock()


@pytest.fixture
def password_service():
    # Use real PasswordService behavior for hashing/verification/strength
    return PasswordService(user_repository=Mock())


@pytest.fixture
def service(user_repository, password_service):
    return ChangePasswordService(user_repository=user_repository, password_service=password_service)


@pytest.fixture
def lecturer_user():
    return User(
        user_id=10,
        first_name="Lec",
        last_name="Turer",
        email=Email("lec.turer@example.com"),
        role=UserRole.LECTURER,
        is_active=True,
        has_password=True,
    )


@pytest.fixture
def admin_user():
    return User(
        user_id=11,
        first_name="Ad",
        last_name="Min",
        email=Email("ad.min@example.com"),
        role=UserRole.ADMIN,
        is_active=True,
        has_password=True,
    )


@pytest.fixture
def student_user():
    return User(
        user_id=12,
        first_name="Stu",
        last_name="Dent",
        email=Email("stu.dent@example.com"),
        role=UserRole.STUDENT,
        is_active=True,
        has_password=False,
    )


# ---------------------
# Tests
# ---------------------

class TestChangePasswordService:
    def test_change_password_success(self, service, user_repository, lecturer_user):
        user_repository.get_by_id.return_value = lecturer_user
        old_hash = make_password("OldPass123!")
        mock_user_model = Mock()
        mock_user_model.password = old_hash

        with patch('user_management.infrastructure.orm.django_models.User') as MockUserModel:
            MockUserModel.objects.get.return_value = mock_user_model

            service.change_password(lecturer_user.user_id, "OldPass123!", "NewPass123!")

            assert user_repository.update_password.called is True
            args = user_repository.update_password.call_args[0]
            assert args[0] == lecturer_user.user_id
            assert check_password("NewPass123!", args[1]) is True

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

    def test_weak_new_password_raises(self, service, user_repository, lecturer_user, monkeypatch):
        user_repository.get_by_id.return_value = lecturer_user
        old_hash = make_password("OldPass123!")
        mock_user_model = Mock()
        mock_user_model.password = old_hash

        with patch('user_management.infrastructure.orm.django_models.User') as MockUserModel:
            MockUserModel.objects.get.return_value = mock_user_model

            with pytest.raises(WeakPasswordError):
                service.change_password(lecturer_user.user_id, "OldPass123!", "weak")

            user_repository.update_password.assert_not_called()

    def test_student_cannot_change_password(self, service, user_repository, student_user):
        user_repository.get_by_id.return_value = student_user

        with pytest.raises(StudentCannotHavePasswordError):
            service.change_password(student_user.user_id, "irrelevant", "NewPass123!")

        user_repository.update_password.assert_not_called()

    def test_user_not_found_via_repository(self, user_repository, password_service):
        # Simulate repository raising not found
        user_repository.get_by_id.side_effect = UserNotFoundError("id:999")
        svc = ChangePasswordService(user_repository=user_repository, password_service=password_service)

        with pytest.raises(UserNotFoundError):
            svc.change_password(999, "OldPass123!", "NewPass123!")

        user_repository.update_password.assert_not_called()

    def test_user_model_not_found_raises_user_not_found(self, service, user_repository, lecturer_user):
        user_repository.get_by_id.return_value = lecturer_user
        with patch('user_management.infrastructure.orm.django_models.User') as MockUserModel:
            # Ensure DoesNotExist is an Exception subclass so the except clause matches
            class _DoesNotExist(Exception):
                pass
            MockUserModel.DoesNotExist = _DoesNotExist
            MockUserModel.objects.get.side_effect = _DoesNotExist()

            with pytest.raises(UserNotFoundError):
                service.change_password(lecturer_user.user_id, "OldPass123!", "NewPass123!")

            user_repository.update_password.assert_not_called()
