"""Tests for StudentProfile domain entity."""
import pytest

from user_management.domain.entities.student_profile import StudentProfile
from user_management.domain.value_objects.student_id import StudentId
from user_management.domain.exceptions import InvalidYearError


class TestStudentProfile:
    """Tests for StudentProfile entity creation, validation, and methods."""
    
    # === Creation Tests ===
    
    def test_create_valid_profile(self):
        """Test creating a valid student profile."""
        sid = StudentId("BCS/000001")
        sp = StudentProfile(
            student_profile_id=None,
            student_id=sid,
            user_id=10,
            program_id=1,
            stream_id=None,
            year_of_study=1,
            qr_code_data=str(sid),
        )
        assert sp.program_code == "BCS"
        assert sp.year_of_study == 1
        assert str(sp) == "Student BCS/000001"
    
    def test_create_profile_with_stream(self):
        """Test creating a student profile with stream."""
        sid = StudentId("ENG/123456")
        sp = StudentProfile(
            student_profile_id=5,
            student_id=sid,
            user_id=20,
            program_id=2,
            stream_id=3,
            year_of_study=3,
            qr_code_data=str(sid),
        )
        assert sp.stream_id == 3
        assert sp.program_code == "ENG"
    
    # === Year Validation Tests ===
    
    @pytest.mark.parametrize("year", [1, 2, 3, 4])
    def test_valid_years_accepted(self, year):
        """Test that all valid years (1-4) are accepted."""
        sid = StudentId("BCS/000002")
        sp = StudentProfile(
            student_profile_id=None,
            student_id=sid,
            user_id=11,
            program_id=1,
            stream_id=None,
            year_of_study=year,
            qr_code_data=str(sid),
        )
        assert sp.year_of_study == year
    
    @pytest.mark.parametrize("year", [0, -1, 5, 6, 10])
    def test_invalid_years_rejected(self, year):
        """Test that invalid years raise InvalidYearError."""
        sid = StudentId("BCS/000003")
        with pytest.raises(InvalidYearError) as exc_info:
            StudentProfile(
                student_profile_id=None,
                student_id=sid,
                user_id=12,
                program_id=1,
                stream_id=None,
                year_of_study=year,
                qr_code_data=str(sid),
            )
        assert exc_info.value.year == year

    def test_year_out_of_range_raises(self):
        """Test that year > 4 raises InvalidYearError."""
        sid = StudentId("BCS/000004")
        with pytest.raises(InvalidYearError):
            StudentProfile(
                student_profile_id=None,
                student_id=sid,
                user_id=11,
                program_id=1,
                stream_id=None,
                year_of_study=5,
                qr_code_data=str(sid),
            )
    
    def test_year_zero_raises(self):
        """Test that year = 0 raises InvalidYearError."""
        sid = StudentId("BCS/000005")
        with pytest.raises(InvalidYearError):
            StudentProfile(
                student_profile_id=None,
                student_id=sid,
                user_id=13,
                program_id=1,
                stream_id=None,
                year_of_study=0,
                qr_code_data=str(sid),
            )

    # === QR Code Validation Tests ===

    def test_qr_code_must_match_student_id(self):
        """Test that QR code must equal student ID."""
        sid = StudentId("BCS/000006")
        with pytest.raises(ValueError, match="QR code data must match student ID"):
            StudentProfile(
                student_profile_id=None,
                student_id=sid,
                user_id=12,
                program_id=1,
                stream_id=None,
                year_of_study=2,
                qr_code_data="MISMATCH",
            )
    
    # === Update Methods Tests ===

    def test_update_year_and_stream(self):
        """Test updating year and stream."""
        sid = StudentId("BCS/000007")
        sp = StudentProfile(
            student_profile_id=5,
            student_id=sid,
            user_id=13,
            program_id=1,
            stream_id=2,
            year_of_study=2,
            qr_code_data=str(sid),
        )
        sp.update_year(3)
        assert sp.year_of_study == 3
        sp.update_stream(None)
        assert sp.stream_id is None
    
    @pytest.mark.parametrize("invalid_year", [0, 5, -1, 10])
    def test_update_year_invalid_raises(self, invalid_year):
        """Test that update_year with invalid year raises InvalidYearError."""
        sid = StudentId("BCS/000008")
        sp = StudentProfile(
            student_profile_id=6,
            student_id=sid,
            user_id=14,
            program_id=1,
            stream_id=None,
            year_of_study=1,
            qr_code_data=str(sid),
        )
        with pytest.raises(InvalidYearError):
            sp.update_year(invalid_year)
        # Original year should remain unchanged
        assert sp.year_of_study == 1
    
    # === Equality and Hash Tests ===
    
    def test_equality_with_same_id(self):
        """Test that profiles with same ID are equal."""
        sid1 = StudentId("BCS/000013")
        sid2 = StudentId("ENG/999999")
        sp1 = StudentProfile(
            student_profile_id=1,
            student_id=sid1,
            user_id=19,
            program_id=1,
            stream_id=None,
            year_of_study=1,
            qr_code_data=str(sid1),
        )
        sp2 = StudentProfile(
            student_profile_id=1,
            student_id=sid2,
            user_id=20,
            program_id=2,
            stream_id=3,
            year_of_study=4,
            qr_code_data=str(sid2),
        )
        assert sp1 == sp2
    
    def test_hash_consistency(self):
        """Test that hash is consistent."""
        sid = StudentId("BCS/000015")
        sp = StudentProfile(
            student_profile_id=1,
            student_id=sid,
            user_id=22,
            program_id=1,
            stream_id=None,
            year_of_study=1,
            qr_code_data=str(sid),
        )
        hash1 = hash(sp)
        hash2 = hash(sp)
        assert hash1 == hash2
