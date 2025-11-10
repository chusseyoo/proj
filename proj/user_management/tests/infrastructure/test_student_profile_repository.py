"""Infrastructure tests for StudentProfileRepository.

Covers persistence, retrieval, updates, FKs, and uniqueness constraints.
"""
import pytest
from django.db import IntegrityError

from user_management.infrastructure.repositories.student_profile_repository import StudentProfileRepository
from user_management.domain.entities import StudentProfile
from user_management.domain.value_objects import StudentId
from user_management.domain.exceptions import StudentIdAlreadyExistsError, StudentNotFoundError
from django.core.exceptions import ValidationError as DJValidationError

pytestmark = pytest.mark.django_db


@pytest.fixture
def repository() -> StudentProfileRepository:
    return StudentProfileRepository()


def test_create_persists_profile_with_user_fk(repository, student_profile_factory, user_factory, program_factory):
    user = user_factory(role="Student", password=None)
    program = program_factory()
    profile = repository.create(StudentProfile(
        student_profile_id=None,
        student_id=StudentId("BCS/654321"),
        user_id=user.user_id,
        program_id=program.program_id,
        stream_id=None,
        year_of_study=2,
        qr_code_data="BCS/654321",
    ))
    assert profile.student_profile_id is not None
    assert profile.user_id == user.user_id
    assert profile.program_id == program.program_id


def test_exists_by_student_id_true_after_create(repository, student_profile_factory):
    profile = student_profile_factory(student_id="BCS/111111")
    assert repository.exists_by_student_id("BCS/111111") is True


def test_exists_by_student_id_false_for_unknown(repository):
    assert repository.exists_by_student_id("ZZZ/999999") is False


def test_find_by_student_id_returns_profile(repository, student_profile_factory):
    profile = student_profile_factory(student_id="BCS/222222")
    found = repository.find_by_student_id("BCS/222222")
    assert found is not None
    assert str(found.student_id) == "BCS/222222"


def test_find_by_student_id_none_when_missing(repository):
    assert repository.find_by_student_id("ZZZ/999999") is None


def test_duplicate_student_id_raises_domain_error(repository, student_profile_factory, user_factory, program_factory):
    profile1 = student_profile_factory(student_id="BCS/333333")
    user2 = user_factory(email="student2@example.com", role="Student", password=None)
    program = program_factory()
    with pytest.raises(StudentIdAlreadyExistsError):
        repository.create(StudentProfile(
            student_profile_id=None,
            student_id=StudentId("BCS/333333"),
            user_id=user2.user_id,
            program_id=program.program_id,
            stream_id=None,
            year_of_study=2,
            qr_code_data="BCS/333333",
        ))


def test_update_year_of_study_valid(repository, student_profile_factory):
    profile = student_profile_factory(year_of_study=2)
    updated = repository.update_year(profile.student_profile_id, 3)
    assert updated.year_of_study == 3


def test_update_stream_changes_stream_id(repository, student_profile_factory, stream_factory):
    profile = student_profile_factory()
    stream = stream_factory()
    updated = repository.update_stream(profile.student_profile_id, stream.stream_id)
    assert updated.stream_id == stream.stream_id


def test_delete_removes_profile(repository, student_profile_factory):
    profile = student_profile_factory()
    repository.delete(profile.student_profile_id)
    assert repository.find_by_student_id(str(profile.student_id)) is None


def test_delete_nonexistent_profile_raises_error(repository):
    with pytest.raises(StudentNotFoundError):
        repository.delete(999999)


def test_student_id_normalization_uppercase(repository, user_factory, program_factory):
    user = user_factory(role="Student", password=None)
    program = program_factory()
    profile = repository.create(StudentProfile(
        student_profile_id=None,
        student_id=StudentId("bcs/444444"),  # lowercase input
        user_id=user.user_id,
        program_id=program.program_id,
        stream_id=None,
        year_of_study=2,
        qr_code_data="BCS/444444",  # Must match normalized ID
    ))
    # Should be stored as uppercase
    found = repository.get_by_student_id("BCS/444444")
    assert str(found.student_id) == "BCS/444444"


def test_create_stores_qr_code_equal_student_id(repository, user_factory, program_factory):
    user = user_factory(role="Student", password=None)
    program = program_factory()
    profile = repository.create(StudentProfile(
        student_profile_id=None,
        student_id=StudentId("BCS/555555"),
        user_id=user.user_id,
        program_id=program.program_id,
        stream_id=None,
        year_of_study=2,
        qr_code_data="BCS/555555",  # Must be provided and match student_id
    ))
    assert profile.qr_code_data == "BCS/555555"


def test_update_year_of_study_invalid_out_of_range(repository, student_profile_factory):
    """Updating to invalid year should raise Django ValidationError (model validators)."""
    profile = student_profile_factory(year_of_study=2)
    with pytest.raises(DJValidationError):
        repository.update_year(profile.student_profile_id, 5)


def test_delete_user_cascades_student_profile(repository, student_profile_factory):
    """Deleting the underlying user should cascade and remove student profile."""
    from user_management.infrastructure.orm.django_models import User as UserModel
    profile = student_profile_factory()
    user_id = profile.user_id
    # Delete user at ORM level to trigger CASCADE
    UserModel.objects.filter(user_id=user_id).delete()
    # Repository should not find profile anymore
    assert repository.find_by_student_id(profile.student_id) is None
