"""Tests for LecturerProfile domain entity."""
import pytest

from user_management.domain.entities.lecturer_profile import LecturerProfile
from user_management.domain.exceptions import InvalidDepartmentNameError


class TestLecturerProfile:
    """Tests for LecturerProfile entity creation, validation, and methods."""
    
    # === Creation Tests ===
    
    def test_create_valid_lecturer_profile(self):
        """Test creating a valid lecturer profile."""
        lp = LecturerProfile(
            lecturer_profile_id=None,
            user_id=20,
            department_name="Computer Science",
        )
        assert lp.department_name == "Computer Science"
        assert str(lp) == "Computer Science Lecturer"
    
    # === Department Validation Tests ===

    def test_empty_department_raises(self):
        """Test that empty department name raises InvalidDepartmentNameError."""
        with pytest.raises(InvalidDepartmentNameError):
            LecturerProfile(
                lecturer_profile_id=None,
                user_id=21,
                department_name="   ",
            )

    def test_update_department_validation(self):
        """Test updating department name with validation."""
        lp = LecturerProfile(
            lecturer_profile_id=2,
            user_id=22,
            department_name="Mathematics",
        )
        lp.update_department("Physics")
        assert lp.department_name == "Physics"
        with pytest.raises(InvalidDepartmentNameError):
            lp.update_department("")
    
    def test_department_normalization(self):
        """Test that department name is normalized (whitespace stripped)."""
        lp = LecturerProfile(
            lecturer_profile_id=3,
            user_id=23,
            department_name="  Mathematics  ",
        )
        assert lp.department_name == "Mathematics"
    
    # === String Representation Tests ===
    
    def test_str_method(self):
        """Test __str__ method returns expected format."""
        lp = LecturerProfile(
            lecturer_profile_id=4,
            user_id=24,
            department_name="Engineering",
        )
        assert str(lp) == "Engineering Lecturer"
    
    # === Equality and Hash Tests ===
    
    def test_equality_with_same_id(self):
        """Test that profiles with same ID are equal."""
        lp1 = LecturerProfile(
            lecturer_profile_id=1,
            user_id=25,
            department_name="Computer Science",
        )
        lp2 = LecturerProfile(
            lecturer_profile_id=1,
            user_id=26,
            department_name="Mathematics",
        )
        assert lp1 == lp2
    
    def test_equality_with_different_id(self):
        """Test that profiles with different IDs are not equal."""
        lp1 = LecturerProfile(
            lecturer_profile_id=1,
            user_id=27,
            department_name="Physics",
        )
        lp2 = LecturerProfile(
            lecturer_profile_id=2,
            user_id=27,
            department_name="Physics",
        )
        assert lp1 != lp2
    
    def test_hash_consistency(self):
        """Test that hash is consistent."""
        lp = LecturerProfile(
            lecturer_profile_id=1,
            user_id=28,
            department_name="Chemistry",
        )
        hash1 = hash(lp)
        hash2 = hash(lp)
        assert hash1 == hash2
