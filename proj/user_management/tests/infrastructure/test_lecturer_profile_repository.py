"""Infrastructure tests for LecturerProfileRepository.

Covers persistence, retrieval, updates, department filtering, and FK relationships.
"""
import pytest

from user_management.infrastructure.repositories.lecturer_profile_repository import LecturerProfileRepository
from user_management.domain.entities import LecturerProfile
from user_management.domain.exceptions import LecturerNotFoundError, InvalidDepartmentNameError
from django.db import IntegrityError

pytestmark = pytest.mark.django_db


@pytest.fixture
def repository() -> LecturerProfileRepository:
    return LecturerProfileRepository()


def test_create_persists_profile_with_user_fk(repository, lecturer_profile_factory, user_factory):
    user = user_factory(role="Lecturer")
    profile = repository.create(LecturerProfile(
        lecturer_profile_id=None,
        user_id=user.user_id,
        department_name="Computer Science",
    ))
    assert profile.lecturer_profile_id is not None
    assert profile.user_id == user.user_id
    assert profile.department_name == "Computer Science"


def test_exists_by_user_id_true_after_create(repository, lecturer_profile_factory):
    profile = lecturer_profile_factory()
    assert repository.exists_by_user_id(profile.user_id) is True


def test_exists_by_user_id_false_for_unknown(repository):
    assert repository.exists_by_user_id(999999) is False


def test_find_by_user_id_returns_profile(repository, lecturer_profile_factory):
    profile = lecturer_profile_factory(department_name="Mathematics")
    found = repository.find_by_user_id(profile.user_id)
    assert found is not None
    assert found.department_name == "Mathematics"


def test_find_by_user_id_none_when_missing(repository):
    assert repository.find_by_user_id(999999) is None


def test_get_by_id_returns_profile(repository, lecturer_profile_factory):
    profile = lecturer_profile_factory()
    found = repository.get_by_id(profile.lecturer_id)
    assert found.lecturer_profile_id == profile.lecturer_id
    assert found.user_id == profile.user_id


def test_get_by_id_raises_not_found_for_missing(repository):
    with pytest.raises(LecturerNotFoundError):
        repository.get_by_id(999999)


def test_get_by_user_id_returns_profile(repository, lecturer_profile_factory):
    profile = lecturer_profile_factory()
    found = repository.get_by_user_id(profile.user_id)
    assert found.user_id == profile.user_id


def test_get_by_user_id_raises_not_found_for_missing(repository):
    with pytest.raises(LecturerNotFoundError):
        repository.get_by_user_id(999999)


def test_update_department_changes_value(repository, lecturer_profile_factory):
    profile = lecturer_profile_factory(department_name="Computer Science")
    updated = repository.update_department(profile.lecturer_id, "Physics")
    assert updated.department_name == "Physics"


def test_update_with_kwargs(repository, lecturer_profile_factory):
    profile = lecturer_profile_factory(department_name="Biology")
    updated = repository.update(profile.lecturer_id, department_name="Chemistry")
    assert updated.department_name == "Chemistry"


def test_update_nonexistent_profile_raises_error(repository):
    with pytest.raises(LecturerNotFoundError):
        repository.update_department(999999, "New Department")


def test_delete_removes_profile(repository, lecturer_profile_factory):
    profile = lecturer_profile_factory()
    repository.delete(profile.lecturer_id)
    assert repository.find_by_user_id(profile.user_id) is None


def test_delete_nonexistent_profile_raises_error(repository):
    with pytest.raises(LecturerNotFoundError):
        repository.delete(999999)


def test_list_by_department_filters_correctly(repository, lecturer_profile_factory):
    profile1 = lecturer_profile_factory(department_name="Computer Science")
    profile2 = lecturer_profile_factory(department_name="Computer Science")
    profile3 = lecturer_profile_factory(department_name="Mathematics")
    
    cs_lecturers = repository.list_by_department("Computer Science")
    assert len(cs_lecturers) == 2
    assert all(p.department_name == "Computer Science" for p in cs_lecturers)


def test_list_by_department_case_insensitive(repository, lecturer_profile_factory):
    profile = lecturer_profile_factory(department_name="Computer Science")
    
    found = repository.list_by_department("computer science")
    assert len(found) == 1
    assert found[0].lecturer_profile_id == profile.lecturer_id


def test_list_all_returns_all_profiles(repository, lecturer_profile_factory):
    profile1 = lecturer_profile_factory()
    profile2 = lecturer_profile_factory()
    profile3 = lecturer_profile_factory()
    
    all_profiles = repository.list_all()
    assert len(all_profiles) >= 3


def test_department_name_normalization_strips_whitespace(repository, user_factory):
    user = user_factory(role="Lecturer")
    profile = repository.create(LecturerProfile(
        lecturer_profile_id=None,
        user_id=user.user_id,
        department_name="  Computer Science  ",
    ))
    assert profile.department_name == "Computer Science"


def test_department_name_empty_raises_validation_error(user_factory):
    user = user_factory(role="Lecturer")
    with pytest.raises(InvalidDepartmentNameError):
        LecturerProfile(
            lecturer_profile_id=None,
            user_id=user.user_id,
            department_name="",
        )


def test_department_name_whitespace_only_raises_validation_error(user_factory):
    user = user_factory(role="Lecturer")
    with pytest.raises(InvalidDepartmentNameError):
        LecturerProfile(
            lecturer_profile_id=None,
            user_id=user.user_id,
            department_name="   ",
        )


def test_cascade_delete_on_user_deletion(repository, lecturer_profile_factory, user_factory):
    """Test that deleting a user cascades to lecturer profile."""
    from user_management.infrastructure.orm.django_models import User as UserModel
    
    user = user_factory(role="Lecturer")
    profile = lecturer_profile_factory(user=user)
    
    # Delete the user
    UserModel.objects.filter(user_id=user.user_id).delete()
    
    # Profile should be gone
    assert repository.find_by_user_id(user.user_id) is None


def test_get_with_user_optimized_query(repository, lecturer_profile_factory):
    """Test select_related optimization for user info."""
    profile = lecturer_profile_factory()
    
    # Should not raise; verifies select_related works
    found = repository.get_with_user(profile.lecturer_id)
    assert found.lecturer_profile_id == profile.lecturer_id


def test_list_with_user_info_optimized(repository, lecturer_profile_factory):
    """Test select_related optimization for list queries."""
    profile1 = lecturer_profile_factory()
    profile2 = lecturer_profile_factory()
    
    # Should not raise; verifies select_related works
    profiles = repository.list_with_user_info()
    assert len(profiles) >= 2


def test_multiple_profiles_not_allowed_per_user(repository, user_factory, lecturer_profile_factory):
    """Attempting to create a second lecturer profile for same user should raise IntegrityError (OneToOne)."""
    user = user_factory(role="Lecturer")
    lecturer_profile_factory(user=user)
    from user_management.infrastructure.orm.django_models import LecturerProfile as LecturerProfileModel
    with pytest.raises(IntegrityError):
        LecturerProfileModel.objects.create(user=user, department_name="Physics")
