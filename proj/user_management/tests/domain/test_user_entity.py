"""Tests for the User domain entity."""
import pytest

from user_management.domain.entities.user import User, UserRole
from user_management.domain.value_objects.email import Email


class TestUserEntity:
    """Tests for User entity creation, validation, and methods."""
    
    # === Creation and Role Tests ===
    
    def test_create_valid_lecturer(self):
        """Test creating a valid lecturer with password."""
        u = User(
            user_id=None,
            first_name="John",
            last_name="Doe",
            email=Email("john@example.com"),
            role=UserRole.LECTURER,
            is_active=True,
            has_password=True,
        )
        assert u.is_lecturer()
        assert not u.is_student()
        assert not u.is_admin()
        assert u.full_name == "John Doe"
        assert "john@example.com" in str(u)
    
    def test_create_valid_student(self):
        """Test creating a valid student without password."""
        u = User(
            user_id=None,
            first_name="Jane",
            last_name="Student",
            email=Email("jane@student.com"),
            role=UserRole.STUDENT,
            is_active=True,
            has_password=False,
        )
        assert u.is_student()
        assert not u.is_lecturer()
        assert not u.is_admin()
        assert u.full_name == "Jane Student"
    
    def test_create_valid_admin(self):
        """Test creating a valid admin with password."""
        u = User(
            user_id=None,
            first_name="Admin",
            last_name="User",
            email=Email("admin@example.com"),
            role=UserRole.ADMIN,
            is_active=True,
            has_password=True,
        )
        assert u.is_admin()
        assert not u.is_lecturer()
        assert not u.is_student()
        assert u.full_name == "Admin User"
    
    # === Password Invariant Tests ===
    
    def test_student_cannot_have_password(self):
        """Test that students cannot have passwords."""
        with pytest.raises(ValueError, match="Students cannot have passwords"):
            User(
                user_id=None,
                first_name="Jane",
                last_name="Student",
                email=Email("jane@student.com"),
                role=UserRole.STUDENT,
                has_password=True,
            )

    def test_admin_must_have_password(self):
        """Test that admins must have passwords."""
        with pytest.raises(ValueError, match="Admin and Lecturer must have passwords"):
            User(
                user_id=None,
                first_name="Admin",
                last_name="NoPass",
                email=Email("admin@example.com"),
                role=UserRole.ADMIN,
                has_password=False,
            )
    
    def test_lecturer_must_have_password(self):
        """Test that lecturers must have passwords."""
        with pytest.raises(ValueError, match="Admin and Lecturer must have passwords"):
            User(
                user_id=None,
                first_name="Lecturer",
                last_name="NoPass",
                email=Email("lecturer@example.com"),
                role=UserRole.LECTURER,
                has_password=False,
            )
    
    # === Name Validation Tests ===
    
    def test_empty_first_name_raises(self):
        """Test that empty first name raises ValueError."""
        with pytest.raises(ValueError, match="First name cannot be empty"):
            User(
                user_id=None,
                first_name="",
                last_name="Doe",
                email=Email("test@example.com"),
                role=UserRole.ADMIN,
                has_password=True,
            )
    
    def test_whitespace_only_first_name_raises(self):
        """Test that whitespace-only first name raises ValueError."""
        with pytest.raises(ValueError, match="First name cannot be empty"):
            User(
                user_id=None,
                first_name="   ",
                last_name="Doe",
                email=Email("test@example.com"),
                role=UserRole.ADMIN,
                has_password=True,
            )
    
    def test_empty_last_name_raises(self):
        """Test that empty last name raises ValueError."""
        with pytest.raises(ValueError, match="Last name cannot be empty"):
            User(
                user_id=None,
                first_name="John",
                last_name="",
                email=Email("test@example.com"),
                role=UserRole.ADMIN,
                has_password=True,
            )
    
    def test_whitespace_only_last_name_raises(self):
        """Test that whitespace-only last name raises ValueError."""
        with pytest.raises(ValueError, match="Last name cannot be empty"):
            User(
                user_id=None,
                first_name="John",
                last_name="   ",
                email=Email("test@example.com"),
                role=UserRole.ADMIN,
                has_password=True,
            )
    
    # === Activation/Deactivation Tests ===

    def test_activate_deactivate(self):
        """Test user activation and deactivation."""
        u = User(
            user_id=1,
            first_name="A",
            last_name="B",
            email=Email("a@b.com"),
            role=UserRole.ADMIN,
            has_password=True,
        )
        assert u.is_admin()
        u.deactivate()
        assert not u.is_active
        u.activate()
        assert u.is_active
    
    def test_user_defaults_to_active(self):
        """Test that users default to active status."""
        u = User(
            user_id=None,
            first_name="Test",
            last_name="User",
            email=Email("test@example.com"),
            role=UserRole.LECTURER,
            has_password=True,
        )
        assert u.is_active
    
    # === Equality and Hash Tests ===
    
    def test_equality_with_same_id(self):
        """Test that users with same ID are equal."""
        u1 = User(
            user_id=1,
            first_name="John",
            last_name="Doe",
            email=Email("john@example.com"),
            role=UserRole.LECTURER,
            has_password=True,
        )
        u2 = User(
            user_id=1,
            first_name="Jane",
            last_name="Smith",
            email=Email("jane@example.com"),
            role=UserRole.ADMIN,
            has_password=True,
        )
        assert u1 == u2
    
    def test_equality_with_different_id(self):
        """Test that users with different IDs are not equal."""
        u1 = User(
            user_id=1,
            first_name="John",
            last_name="Doe",
            email=Email("john@example.com"),
            role=UserRole.LECTURER,
            has_password=True,
        )
        u2 = User(
            user_id=2,
            first_name="John",
            last_name="Doe",
            email=Email("john@example.com"),
            role=UserRole.LECTURER,
            has_password=True,
        )
        assert u1 != u2
    
    def test_equality_with_none_id(self):
        """Test that users with None ID are not equal."""
        u1 = User(
            user_id=None,
            first_name="John",
            last_name="Doe",
            email=Email("john@example.com"),
            role=UserRole.LECTURER,
            has_password=True,
        )
        u2 = User(
            user_id=None,
            first_name="John",
            last_name="Doe",
            email=Email("john@example.com"),
            role=UserRole.LECTURER,
            has_password=True,
        )
        assert u1 != u2  # Different instances with None ID
    
    def test_hash_consistency(self):
        """Test that hash is consistent for users with IDs."""
        u = User(
            user_id=1,
            first_name="John",
            last_name="Doe",
            email=Email("john@example.com"),
            role=UserRole.LECTURER,
            has_password=True,
        )
        hash1 = hash(u)
        hash2 = hash(u)
        assert hash1 == hash2
    
    def test_users_can_be_added_to_set(self):
        """Test that users can be stored in sets."""
        u1 = User(
            user_id=1,
            first_name="John",
            last_name="Doe",
            email=Email("john@example.com"),
            role=UserRole.LECTURER,
            has_password=True,
        )
        u2 = User(
            user_id=2,
            first_name="Jane",
            last_name="Smith",
            email=Email("jane@example.com"),
            role=UserRole.ADMIN,
            has_password=True,
        )
        user_set = {u1, u2}
        assert len(user_set) == 2
        assert u1 in user_set
        assert u2 in user_set
