"""Tests for value objects: Email and StudentId."""
import pytest

from user_management.domain.value_objects.email import Email
from user_management.domain.value_objects.student_id import StudentId
from user_management.domain.exceptions import InvalidStudentIdFormatError


class TestEmailVO:
    """Tests for Email value object."""
    
    @pytest.mark.parametrize("raw,expected", [
        ("John.Doe@example.com", "john.doe@example.com"),
        ("UPPER@DOMAIN.CO", "upper@domain.co"),
        (" trim@x.com ", "trim@x.com"),
    ])
    def test_normalizes_and_stores_lowercase(self, raw, expected):
        """Test that email is normalized to lowercase and trimmed."""
        e = Email(raw)
        assert str(e) == expected
        assert e.value == expected

    @pytest.mark.parametrize("bad", ["", "not-an-email", "@no-local.com", "local@.com"])
    def test_invalid_emails_raise(self, bad):
        """Test that invalid emails raise ValueError."""
        with pytest.raises(ValueError):
            Email(bad)

    def test_domain_and_local_part(self):
        """Test extracting domain and local part from email."""
        e = Email("alice+bob@sub.example.org")
        assert e.domain == "sub.example.org"
        assert e.local_part.startswith("alice+bob")
    
    def test_email_equality(self):
        """Test that emails with same value are equal."""
        e1 = Email("test@example.com")
        e2 = Email("TEST@EXAMPLE.COM")
        assert e1 == e2
        assert str(e1) == str(e2)
    
    def test_email_inequality(self):
        """Test that emails with different values are not equal."""
        e1 = Email("test@example.com")
        e2 = Email("other@example.com")
        assert e1 != e2
    
    def test_email_hash_consistency(self):
        """Test that email hash is consistent."""
        e = Email("test@example.com")
        hash1 = hash(e)
        hash2 = hash(e)
        assert hash1 == hash2
    
    def test_email_can_be_used_in_set(self):
        """Test that emails can be used in sets."""
        e1 = Email("test1@example.com")
        e2 = Email("test2@example.com")
        e3 = Email("TEST1@EXAMPLE.COM")  # Same as e1 when normalized
        email_set = {e1, e2, e3}
        assert len(email_set) == 2  # e1 and e3 are the same
    
    def test_email_immutability(self):
        """Test that Email value object is immutable."""
        e = Email("test@example.com")
        # Attempting to set value should fail (frozen dataclass)
        with pytest.raises(AttributeError):
            e.value = "other@example.com"


class TestStudentIdVO:
    """Tests for StudentId value object."""
    
    def test_valid_student_id_normalizes_and_parses(self):
        """Test that student ID normalizes to uppercase and parses correctly."""
        s = StudentId("bcs/000123")
        assert str(s) == "BCS/000123"
        assert s.program_code == "BCS"
        assert s.number == "000123"

    @pytest.mark.parametrize("bad", ["", "BCS-000123", "BC/123456", "ABCD/123456", "ABC/12345a"])
    def test_invalid_formats_raise(self, bad):
        """Test that invalid formats raise InvalidStudentIdFormatError."""
        with pytest.raises(InvalidStudentIdFormatError):
            StudentId(bad)

    def test_validate_format_classmethod(self):
        """Test the validate_format classmethod."""
        assert StudentId.validate_format("bcs/123456") is True
        assert StudentId.validate_format("wrong") is False
    
    def test_student_id_equality(self):
        """Test that student IDs with same value are equal."""
        s1 = StudentId("BCS/123456")
        s2 = StudentId("bcs/123456")
        assert s1 == s2
        assert str(s1) == str(s2)
    
    def test_student_id_inequality(self):
        """Test that student IDs with different values are not equal."""
        s1 = StudentId("BCS/123456")
        s2 = StudentId("ENG/123456")
        assert s1 != s2
    
    def test_student_id_hash_consistency(self):
        """Test that student ID hash is consistent."""
        s = StudentId("BCS/123456")
        hash1 = hash(s)
        hash2 = hash(s)
        assert hash1 == hash2
    
    def test_student_id_can_be_used_in_set(self):
        """Test that student IDs can be used in sets."""
        s1 = StudentId("BCS/123456")
        s2 = StudentId("ENG/654321")
        s3 = StudentId("bcs/123456")  # Same as s1 when normalized
        sid_set = {s1, s2, s3}
        assert len(sid_set) == 2  # s1 and s3 are the same
    
    def test_student_id_immutability(self):
        """Test that StudentId value object is immutable."""
        s = StudentId("BCS/123456")
        # Attempting to set value should fail (frozen dataclass)
        with pytest.raises(AttributeError):
            s.value = "ENG/654321"
    
    def test_program_code_and_number_properties(self):
        """Test program_code and number properties."""
        s = StudentId("ENG/987654")
        assert s.program_code == "ENG"
        assert s.number == "987654"
