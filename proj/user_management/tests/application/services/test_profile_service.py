import pytest
from unittest.mock import Mock

from user_management.application.services.user_service import UserService
from user_management.domain.entities.user import User, UserRole
from user_management.domain.value_objects.email import Email
from user_management.domain.exceptions.core import (
    StudentNotFoundError,
    LecturerNotFoundError,
)

# Note: There isn't a dedicated ProfileService; UserService attaches profiles.
# These tests focus on UserService behavior when including profile payloads and
# on repository update/list operations for profiles via their repos directly.

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
def student_user():
    return User(
        user_id=101,
        first_name="Stu",
        last_name="Dent",
        email=Email("stu.dent@example.com"),
        role=UserRole.STUDENT,
        is_active=True,
        has_password=False,
    )

@pytest.fixture
def lecturer_user():
    return User(
        user_id=102,
        first_name="Lec",
        last_name="Turer",
        email=Email("lec.turer@example.com"),
        role=UserRole.LECTURER,
        is_active=True,
        has_password=True,
    )

# ---------------------
# Tests
# ---------------------

class TestUserServiceProfiles:
    def test_student_profile_attached_when_exists(self, service, user_repository, student_repository, student_user):
        user_repository.get_by_id.return_value = student_user
        student_repository.get_by_user_id.return_value = Mock()

        result = service.get_user_by_id(student_user.user_id, include_profile=True)
        assert result['user'] == student_user
        assert result['student_profile'] is not None

    def test_student_profile_none_when_missing(self, service, user_repository, student_repository, student_user):
        user_repository.get_by_id.return_value = student_user
        student_repository.get_by_user_id.side_effect = StudentNotFoundError("missing")

        result = service.get_user_by_id(student_user.user_id, include_profile=True)
        assert result['student_profile'] is None

    def test_lecturer_profile_attached_when_exists(self, service, user_repository, lecturer_repository, lecturer_user):
        user_repository.get_by_id.return_value = lecturer_user
        lecturer_repository.get_by_user_id.return_value = Mock()

        result = service.get_user_by_id(lecturer_user.user_id, include_profile=True)
        assert result['user'] == lecturer_user
        assert result['lecturer_profile'] is not None

    def test_lecturer_profile_none_when_missing(self, service, user_repository, lecturer_repository, lecturer_user):
        user_repository.get_by_id.return_value = lecturer_user
        lecturer_repository.get_by_user_id.side_effect = LecturerNotFoundError("missing")

        result = service.get_user_by_id(lecturer_user.user_id, include_profile=True)
        assert result['lecturer_profile'] is None
