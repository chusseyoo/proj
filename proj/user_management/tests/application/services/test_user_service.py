import pytest
from unittest.mock import Mock, patch

from user_management.application.services.user_service import UserService
from user_management.domain.entities.user import User, UserRole
from user_management.domain.value_objects.email import Email
from user_management.domain.exceptions.core import (
    UserNotFoundError,
    EmailAlreadyExistsError,
    UnauthorizedError,
)

# ---------------------
# Fixtures
# ---------------------

@pytest.fixture
def user_repository():
    return Mock()

@pytest.fixture
def student_repository():
    return Mock()

@pytest.fixture
def lecturer_repository():
    return Mock()

@pytest.fixture
def service(user_repository, student_repository, lecturer_repository):
    return UserService(
        user_repository=user_repository,
        student_repository=student_repository,
        lecturer_repository=lecturer_repository,
    )

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
# A. Retrieval
# ---------------------

class TestRetrieval:
    def test_get_user_by_id_with_profile_student(self, service, user_repository, student_repository, student_user):
        user_repository.get_by_id.return_value = student_user
        student_repository.get_by_user_id.return_value = Mock()

        result = service.get_user_by_id(student_user.user_id, include_profile=True)
        assert 'user' in result
        assert result['user'] == student_user
        assert 'student_profile' in result
        assert result['student_profile'] is not None

    def test_get_user_by_id_with_profile_lecturer(self, service, user_repository, lecturer_repository, lecturer_user):
        user_repository.get_by_id.return_value = lecturer_user
        lecturer_repository.get_by_user_id.return_value = Mock()

        result = service.get_user_by_id(lecturer_user.user_id, include_profile=True)
        assert 'user' in result
        assert result['user'] == lecturer_user
        assert 'lecturer_profile' in result
        assert result['lecturer_profile'] is not None

    def test_get_user_by_id_profile_missing(self, service, user_repository, student_repository, student_user):
        user_repository.get_by_id.return_value = student_user
        student_repository.get_by_user_id.side_effect = UserNotFoundError("not found")

        result = service.get_user_by_id(student_user.user_id, include_profile=True)
        assert result['student_profile'] is None

    def test_get_user_by_email_normalizes(self, service, user_repository, lecturer_user):
        user_repository.get_by_email.return_value = lecturer_user
        result = service.get_user_by_email(" Bob.Lecturer@Example.com  ")
        assert result['user'] == lecturer_user
        user_repository.get_by_email.assert_called_with("bob.lecturer@example.com")

# ---------------------
# B. Update
# ---------------------

class TestUpdate:
    def test_update_user_email_unique_success(self, service, user_repository, admin_user):
        user_repository.exists_by_email.return_value = False
        user_repository.update.return_value = admin_user

        result = service.update_user(admin_user, admin_user.user_id, {"email": "NEW.Email@Example.com"})
        assert result == admin_user
        # ensure normalization applied
        args = user_repository.update.call_args[0]
        kwargs = user_repository.update.call_args[1]
        assert args[0] == admin_user.user_id
        assert kwargs['email'] == 'new.email@example.com'

    def test_update_user_email_conflict_raises(self, service, user_repository, admin_user):
        user_repository.exists_by_email.return_value = True
        # Simulate existing different user
        other = Mock()
        other.user_id = 999
        user_repository.find_by_email.return_value = other

        with pytest.raises(EmailAlreadyExistsError):
            service.update_user(admin_user, admin_user.user_id, {"email": "duplicate@example.com"})

    def test_update_user_role_ignored(self, service, user_repository, admin_user):
        user_repository.update.return_value = admin_user
        result = service.update_user(admin_user, admin_user.user_id, {"role": UserRole.STUDENT, "first_name": "New"})
        assert result == admin_user
        # role should be popped
        _, kwargs = user_repository.update.call_args
        assert 'role' not in kwargs
        assert kwargs['first_name'] == 'New'

# ---------------------
# C. Activation / Deactivation
# ---------------------

class TestActivation:
    def test_activate_user_admin_success(self, service, user_repository, admin_user):
        user_repository.activate.return_value = admin_user
        result = service.activate_user(admin_user, admin_user.user_id)
        assert result == admin_user
        user_repository.activate.assert_called_with(admin_user.user_id)

    def test_activate_user_non_admin_raises(self, service, user_repository, lecturer_user):
        with pytest.raises(UnauthorizedError):
            service.activate_user(lecturer_user, lecturer_user.user_id)

    def test_deactivate_user_admin_success(self, service, user_repository, admin_user):
        user_repository.deactivate.return_value = admin_user
        result = service.deactivate_user(admin_user, admin_user.user_id)
        assert result == admin_user
        user_repository.deactivate.assert_called_with(admin_user.user_id)

    def test_deactivate_user_non_admin_raises(self, service, user_repository, lecturer_user):
        with pytest.raises(UnauthorizedError):
            service.deactivate_user(lecturer_user, lecturer_user.user_id)

# ---------------------
# D. Not Found Handling
# ---------------------

class TestNotFound:
    def test_get_user_by_id_not_found(self, service, user_repository):
        user_repository.get_by_id.side_effect = UserNotFoundError("missing")
        with pytest.raises(UserNotFoundError):
            service.get_user_by_id(999)

    def test_get_user_by_email_not_found(self, service, user_repository):
        user_repository.get_by_email.side_effect = UserNotFoundError("missing")
        with pytest.raises(UserNotFoundError):
            service.get_user_by_email("missing@example.com")
