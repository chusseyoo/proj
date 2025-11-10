"""Infrastructure tests for UserRepository.

Covers persistence, retrieval, updates, activation/deactivation, and uniqueness constraints.
"""
import pytest
from django.db import IntegrityError

from user_management.infrastructure.repositories.user_repository import UserRepository
from user_management.domain.entities import User, UserRole
from user_management.domain.value_objects import Email
from user_management.domain.exceptions import EmailAlreadyExistsError, UserNotFoundError

pytestmark = pytest.mark.django_db


@pytest.fixture
def repository() -> UserRepository:
    return UserRepository()


@pytest.fixture
def lecturer_user_entity():
    return User(
        user_id=None,
        first_name="Alice",
        last_name="Lecturer",
        email=Email("alice.lecturer@example.com"),
        role=UserRole.LECTURER,
        is_active=True,
        has_password=True,
    )


def test_create_persists_user_with_password_hash(repository, lecturer_user_entity):
    created = repository.create(lecturer_user_entity, password_hash="hashed_pw")
    assert created.user_id is not None
    assert created.has_password is True
    # Re-fetch by id
    fetched = repository.get_by_id(created.user_id)
    assert fetched.email == lecturer_user_entity.email
    assert fetched.first_name == "Alice"


def test_create_student_without_password_hash(repository):
    student = User(
        user_id=None,
        first_name="Bob",
        last_name="Student",
        email=Email("bob.student@example.com"),
        role=UserRole.STUDENT,
        is_active=True,
        has_password=False,
    )
    created = repository.create(student, password_hash=None)
    assert created.has_password is False


def test_exists_by_email_true_after_create(repository, lecturer_user_entity):
    repository.create(lecturer_user_entity, password_hash="hash")
    assert repository.exists_by_email("alice.lecturer@example.com") is True


def test_exists_by_email_false_for_unknown(repository):
    assert repository.exists_by_email("missing@example.com") is False


def test_get_by_email_case_insensitive(repository, lecturer_user_entity):
    repository.create(lecturer_user_entity, password_hash="hash")
    fetched = repository.get_by_email("ALICE.LECTURER@EXAMPLE.COM")
    assert fetched.email == lecturer_user_entity.email


def test_get_by_id(repository, lecturer_user_entity):
    created = repository.create(lecturer_user_entity, password_hash="hash")
    fetched = repository.get_by_id(created.user_id)
    assert fetched.user_id == created.user_id


def test_find_by_id_none_when_missing(repository):
    assert repository.find_by_id(999999) is None


def test_find_by_email_none_when_missing(repository):
    assert repository.find_by_email("absent@example.com") is None


def test_duplicate_email_raises_domain_error(repository, lecturer_user_entity):
    repository.create(lecturer_user_entity, password_hash="hash")
    with pytest.raises(EmailAlreadyExistsError):
        repository.create(lecturer_user_entity, password_hash="other")


def test_update_changes_first_and_last_name(repository, lecturer_user_entity):
    created = repository.create(lecturer_user_entity, password_hash="hash")
    updated = repository.update(created.user_id, first_name="Alicia", last_name="Lect")
    assert updated.first_name == "Alicia"
    assert updated.last_name == "Lect"


def test_update_nonexistent_user_raises_error(repository):
    with pytest.raises(UserNotFoundError):
        repository.update(999999, first_name="X")


def test_activate_and_deactivate(repository, lecturer_user_entity):
    created = repository.create(lecturer_user_entity, password_hash="hash")
    deactivated = repository.deactivate(created.user_id)
    assert deactivated.is_active is False
    activated = repository.activate(created.user_id)
    assert activated.is_active is True


def test_update_password_sets_has_password(repository, lecturer_user_entity):
    created = repository.create(lecturer_user_entity, password_hash="original")
    updated = repository.update_password(created.user_id, password_hash="newhash")
    assert updated.has_password is True


def test_delete_removes_user(repository, lecturer_user_entity):
    created = repository.create(lecturer_user_entity, password_hash="hash")
    repository.delete(created.user_id)
    assert repository.find_by_id(created.user_id) is None


def test_delete_nonexistent_user_raises_error(repository):
    with pytest.raises(UserNotFoundError):
        repository.delete(777777)


def test_list_by_role(repository):
    lecturer1 = User(
        user_id=None,
        first_name="L1",
        last_name="Test",
        email=Email("l1@example.com"),
        role=UserRole.LECTURER,
        is_active=True,
        has_password=True,
    )
    lecturer2 = User(
        user_id=None,
        first_name="L2",
        last_name="Test",
        email=Email("l2@example.com"),
        role=UserRole.LECTURER,
        is_active=True,
        has_password=True,
    )
    admin = User(
        user_id=None,
        first_name="A1",
        last_name="Admin",
        email=Email("admin@example.com"),
        role=UserRole.ADMIN,
        is_active=True,
        has_password=True,
    )
    repository.create(lecturer1, password_hash="h1")
    repository.create(lecturer2, password_hash="h2")
    repository.create(admin, password_hash="h3")

    lecturers = repository.list_by_role(UserRole.LECTURER)
    assert len(lecturers) == 2
    emails = {str(u.email) for u in lecturers}
    assert emails == {"l1@example.com", "l2@example.com"}


def test_list_active(repository):
    active_user = User(
        user_id=None,
        first_name="Active",
        last_name="User",
        email=Email("active@example.com"),
        role=UserRole.ADMIN,
        is_active=True,
        has_password=True,
    )
    inactive_user = User(
        user_id=None,
        first_name="Inactive",
        last_name="User",
        email=Email("inactive@example.com"),
        role=UserRole.ADMIN,
        is_active=False,
        has_password=True,
    )
    repository.create(active_user, password_hash="h1")
    created_inactive = repository.create(inactive_user, password_hash="h2")
    # Deactivate to simulate stored state (already inactive)
    repository.deactivate(created_inactive.user_id)

    active_list = repository.list_active()
    assert any(u.email == active_user.email for u in active_list)
    assert all(u.email != inactive_user.email for u in active_list)


def test_list_active_by_role(repository):
    active_lecturer = User(
        user_id=None,
        first_name="ActLect",
        last_name="One",
        email=Email("actlect@example.com"),
        role=UserRole.LECTURER,
        is_active=True,
        has_password=True,
    )
    inactive_lecturer = User(
        user_id=None,
        first_name="InLect",
        last_name="Two",
        email=Email("inlect@example.com"),
        role=UserRole.LECTURER,
        is_active=False,
        has_password=True,
    )
    repository.create(active_lecturer, password_hash="h1")
    created_inactive = repository.create(inactive_lecturer, password_hash="h2")
    repository.deactivate(created_inactive.user_id)

    actives = repository.list_active_by_role(UserRole.LECTURER)
    assert len(actives) == 1
    assert actives[0].email == active_lecturer.email


def test_update_email_normalization_effect(repository):
    """Updating email should persist in lowercase due to model clean()."""
    user = User(
        user_id=None,
        first_name="Norm",
        last_name="Email",
        email=Email("MIXED@Example.COM"),
        role=UserRole.ADMIN,
        is_active=True,
        has_password=True,
    )
    created = repository.create(user, password_hash="hash")
    updated = repository.update(created.user_id, email="NEW.Email@EXAMPLE.com")
    assert str(updated.email) == "new.email@example.com"
    fetched = repository.get_by_id(created.user_id)
    assert str(fetched.email) == "new.email@example.com"


def test_create_admin_role_persistence(repository):
    """Explicitly verify Admin role persistence and password requirement."""
    admin = User(
        user_id=None,
        first_name="Super",
        last_name="Admin",
        email=Email("super.admin@example.com"),
        role=UserRole.ADMIN,
        is_active=True,
        has_password=True,
    )
    created = repository.create(admin, password_hash="hashed_pw")
    assert created.user_id is not None
    assert created.role == UserRole.ADMIN
    assert created.has_password is True


def test_delete_user_cascades_student_profile(repository, program_factory, student_profile_factory):
    """Deleting a student user should cascade and remove the student profile (OneToOne CASCADE)."""
    # Create a Student user via repository
    student = User(
        user_id=None,
        first_name="Stu",
        last_name="Dent",
        email=Email("stu.dent@example.com"),
        role=UserRole.STUDENT,
        is_active=True,
        has_password=False,
    )
    created_user = repository.create(student, password_hash=None)

    # Fetch ORM user instance to attach profile
    from user_management.infrastructure.orm.django_models import User as UserModel
    orm_user = UserModel.objects.get(user_id=created_user.user_id)

    # Create a related StudentProfile (factory will create a program if needed)
    student_profile_factory(user=orm_user, program=program_factory())

    # Delete the user via repository and assert cascade removed profile
    repository.delete(created_user.user_id)

    from user_management.infrastructure.orm.django_models import StudentProfile as StudentProfileModel
    assert not StudentProfileModel.objects.filter(user_id=created_user.user_id).exists()
