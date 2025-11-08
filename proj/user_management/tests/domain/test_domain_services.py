"""Tests for domain services: IdentityService and EnrollmentService."""
import pytest

from user_management.domain.services.identity_service import IdentityService
from user_management.domain.services.enrollment_service import EnrollmentService
from user_management.domain.entities.user import User, UserRole
from user_management.domain.value_objects.email import Email
from user_management.domain.value_objects.student_id import StudentId
from user_management.domain.exceptions import (
    StreamRequiredError,
    StreamNotAllowedError,
    InvalidYearError,
    StudentCannotHavePasswordError,
)


class TestIdentityService:
    """Tests for IdentityService domain service."""
    
    def test_normalize_email_returns_email_vo(self):
        """Test that normalize_email returns an Email value object."""
        e = IdentityService.normalize_email("JoHn@ExAmple.COM ")
        assert isinstance(e, Email)
        assert str(e) == "john@example.com"
    
    @pytest.mark.parametrize("input_email,expected", [
        ("TEST@EXAMPLE.COM", "test@example.com"),
        ("  spaces@test.com  ", "spaces@test.com"),
        ("MixedCase@Domain.ORG", "mixedcase@domain.org"),
    ])
    def test_normalize_email_various_inputs(self, input_email, expected):
        """Test normalize_email with various input formats."""
        e = IdentityService.normalize_email(input_email)
        assert str(e) == expected

    def test_can_user_login_with_password(self):
        """Test can_user_login_with_password for different user roles."""
        u = User(
            user_id=1,
            first_name="A",
            last_name="B",
            email=Email("a@b.com"),
            role=UserRole.ADMIN,
            has_password=True,
        )
        assert IdentityService.can_user_login_with_password(u) is True

        u2 = User(
            user_id=2,
            first_name="S",
            last_name="T",
            email=Email("s@t.com"),
            role=UserRole.STUDENT,
            has_password=False,
        )
        assert IdentityService.can_user_login_with_password(u2) is False
    
    def test_validate_password_requirement_for_student(self):
        """Test that students cannot have passwords."""
        # Should not raise for students without password
        IdentityService.validate_password_requirement(UserRole.STUDENT, has_password=False)
        
        # Should raise for students with password
        with pytest.raises(StudentCannotHavePasswordError):
            IdentityService.validate_password_requirement(UserRole.STUDENT, has_password=True)
    
    def test_validate_password_requirement_for_admin(self):
        """Test that admins must have passwords."""
        # Should not raise for admins with password
        IdentityService.validate_password_requirement(UserRole.ADMIN, has_password=True)
        
        # Should raise for admins without password
        with pytest.raises(ValueError):
            IdentityService.validate_password_requirement(UserRole.ADMIN, has_password=False)
    
    def test_validate_password_requirement_for_lecturer(self):
        """Test that lecturers must have passwords."""
        # Should not raise for lecturers with password
        IdentityService.validate_password_requirement(UserRole.LECTURER, has_password=True)
        
        # Should raise for lecturers without password
        with pytest.raises(ValueError):
            IdentityService.validate_password_requirement(UserRole.LECTURER, has_password=False)


class TestEnrollmentService:
    """Tests for EnrollmentService domain service."""
    
    # === Stream Requirement Tests ===
    
    def test_validate_stream_requirement_has_streams_requires_stream(self):
        """Test that programs with streams require stream assignment."""
        with pytest.raises(StreamRequiredError):
            EnrollmentService.validate_stream_requirement(True, None)
    
    def test_validate_stream_requirement_has_streams_with_stream(self):
        """Test that programs with streams accept stream assignment."""
        # Should not raise
        EnrollmentService.validate_stream_requirement(True, 123)

    def test_validate_stream_requirement_no_streams_disallows_stream(self):
        """Test that programs without streams reject stream assignment."""
        with pytest.raises(StreamNotAllowedError):
            EnrollmentService.validate_stream_requirement(False, 123)
    
    def test_validate_stream_requirement_no_streams_with_none(self):
        """Test that programs without streams accept None stream."""
        # Should not raise
        EnrollmentService.validate_stream_requirement(False, None)
    
    # === Year Validation Tests ===

    def test_validate_year_of_study(self):
        """Test year validation for boundary cases."""
        with pytest.raises(InvalidYearError):
            EnrollmentService.validate_year_of_study(0)
        # valid cases should not raise
        EnrollmentService.validate_year_of_study(1)
        EnrollmentService.validate_year_of_study(4)
    
    @pytest.mark.parametrize("valid_year", [1, 2, 3, 4])
    def test_validate_year_of_study_all_valid(self, valid_year):
        """Test that all valid years (1-4) pass validation."""
        # Should not raise
        EnrollmentService.validate_year_of_study(valid_year)
    
    @pytest.mark.parametrize("invalid_year", [0, -1, 5, 6, 10, 100])
    def test_validate_year_of_study_all_invalid(self, invalid_year):
        """Test that all invalid years raise InvalidYearError."""
        with pytest.raises(InvalidYearError) as exc_info:
            EnrollmentService.validate_year_of_study(invalid_year)
        assert exc_info.value.year == invalid_year
    
    # === Year Progression Tests ===

    def test_can_progress_to_year(self):
        """Test basic year progression logic."""
        assert EnrollmentService.can_progress_to_year(1, 1) is True
        assert EnrollmentService.can_progress_to_year(1, 2) is True
        assert EnrollmentService.can_progress_to_year(1, 3) is False
    
    @pytest.mark.parametrize("current,target,expected", [
        (1, 1, True),   # Stay in year 1
        (1, 2, True),   # Progress 1→2
        (2, 2, True),   # Stay in year 2
        (2, 3, True),   # Progress 2→3
        (3, 3, True),   # Stay in year 3
        (3, 4, True),   # Progress 3→4
        (4, 4, True),   # Stay in year 4
        (1, 3, False),  # Cannot skip years
        (2, 4, False),  # Cannot skip years
        (1, 5, False),  # Cannot progress beyond year 4
        (4, 5, False),  # Cannot progress beyond year 4
        (2, 1, False),  # Cannot go backwards
        (3, 1, False),  # Cannot go backwards
    ])
    def test_can_progress_to_year_all_scenarios(self, current, target, expected):
        """Test all year progression scenarios."""
        assert EnrollmentService.can_progress_to_year(current, target) == expected
