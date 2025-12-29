"""Tests for Attendance ORM model.

Validates:
- Model constraints (unique, check constraints)
- Cascade deletion behavior
- Decimal precision for GPS
- Status field choices
- Model methods (is_late, is_present, get_distance_from_session, was_on_time)
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from django.db import IntegrityError
from django.utils import timezone

from attendance_recording.infrastructure.orm.django_models import Attendance
from user_management.models import User, StudentProfile
from session_management.models import Session


@pytest.mark.django_db
class TestAttendanceModel:
    """Test Attendance ORM model constraints and behavior."""

    def test_create_attendance_record_success(self, sample_student, sample_session):
        """Verify valid attendance creation with auto-timestamp."""
        before_create = timezone.now()
        
        attendance = Attendance.objects.create(
            student_profile=sample_student,
            session=sample_session,
            latitude=Decimal('-1.28334000'),
            longitude=Decimal('36.81667000'),
            status='present',
            is_within_radius=True,
        )
        
        after_create = timezone.now()
        
        assert attendance.attendance_id is not None
        assert attendance.student_profile == sample_student
        assert attendance.session == sample_session
        assert before_create <= attendance.time_recorded <= after_create
        assert attendance.status == 'present'
        assert attendance.is_within_radius is True
        assert isinstance(attendance.latitude, Decimal)
        assert isinstance(attendance.longitude, Decimal)

    def test_unique_constraint_student_session(self, sample_student, sample_session):
        """Enforce one attendance per student per session (duplicate prevention)."""
        # Create first attendance
        Attendance.objects.create(
            student_profile=sample_student,
            session=sample_session,
            latitude=Decimal('-1.28334000'),
            longitude=Decimal('36.81667000'),
            status='present',
            is_within_radius=True,
        )
        
        # Attempt duplicate
        with pytest.raises(IntegrityError) as exc_info:
            Attendance.objects.create(
                student_profile=sample_student,
                session=sample_session,
                latitude=Decimal('-1.28340000'),
                longitude=Decimal('36.81670000'),
                status='late',
                is_within_radius=False,
            )
        
        # SQLite reports UNIQUE constraint failure differently than constraint name
        error_msg = str(exc_info.value).lower()
        assert 'unique' in error_msg or 'student_profile_id' in error_msg

    def test_cascade_delete_student(self, sample_student, sample_session):
        """Verify CASCADE on student_profile FK (data integrity)."""
        attendance = Attendance.objects.create(
            student_profile=sample_student,
            session=sample_session,
            latitude=Decimal('-1.28334000'),
            longitude=Decimal('36.81667000'),
            status='present',
            is_within_radius=True,
        )
        
        attendance_id = attendance.attendance_id
        
        # Delete student profile (should cascade to attendance)
        sample_student.delete()
        
        assert not Attendance.objects.filter(attendance_id=attendance_id).exists()

    def test_cascade_delete_session(self, sample_student, sample_session):
        """Verify CASCADE on session FK (clean up on session removal)."""
        attendance = Attendance.objects.create(
            student_profile=sample_student,
            session=sample_session,
            latitude=Decimal('-1.28334000'),
            longitude=Decimal('36.81667000'),
            status='present',
            is_within_radius=True,
        )
        
        attendance_id = attendance.attendance_id
        
        # Delete session (should cascade to attendance)
        sample_session.delete()
        
        assert not Attendance.objects.filter(attendance_id=attendance_id).exists()

    def test_latitude_longitude_precision(self, sample_student, sample_session):
        """Validate Decimal precision storage (GPS accuracy)."""
        high_precision_lat = Decimal('-1.28334567')
        high_precision_lon = Decimal('36.81667890')
        
        attendance = Attendance.objects.create(
            student_profile=sample_student,
            session=sample_session,
            latitude=high_precision_lat,
            longitude=high_precision_lon,
            status='present',
            is_within_radius=True,
        )
        
        # Reload from database
        attendance.refresh_from_db()
        
        # Should match exactly (no floating-point rounding)
        assert attendance.latitude == high_precision_lat
        assert attendance.longitude == high_precision_lon

    def test_status_field_choices_valid(self, sample_student, sample_session):
        """Validate status field accepts 'present' and 'late'."""
        # Test 'present'
        att1 = Attendance.objects.create(
            student_profile=sample_student,
            session=sample_session,
            latitude=Decimal('-1.28334000'),
            longitude=Decimal('36.81667000'),
            status='present',
            is_within_radius=True,
        )
        assert att1.status == 'present'
        
        # Create another student for second test
        from attendance_recording.tests.conftest import create_test_user, create_test_student_profile
        user2 = create_test_user(
            email='student002@test.com',
            first_name='Student',
            last_name='Two',
        )
        student2 = create_test_student_profile(user2, student_id='BCS/234346')
        
        # Test 'late'
        att2 = Attendance.objects.create(
            student_profile=student2,
            session=sample_session,
            latitude=Decimal('-1.28340000'),
            longitude=Decimal('36.81670000'),
            status='late',
            is_within_radius=False,
        )
        assert att2.status == 'late'

    def test_latitude_check_constraint(self, sample_student, sample_session):
        """Validate latitude range check constraint (-90 to 90)."""
        with pytest.raises(IntegrityError) as exc_info:
            Attendance.objects.create(
                student_profile=sample_student,
                session=sample_session,
                latitude=Decimal('95.0'),  # Invalid: > 90
                longitude=Decimal('36.81667000'),
                status='present',
                is_within_radius=True,
            )
        
        assert 'ck_att_lat_range' in str(exc_info.value)

    def test_longitude_check_constraint(self, sample_student, sample_session):
        """Validate longitude range check constraint (-180 to 180)."""
        with pytest.raises(IntegrityError) as exc_info:
            Attendance.objects.create(
                student_profile=sample_student,
                session=sample_session,
                latitude=Decimal('-1.28334000'),
                longitude=Decimal('185.0'),  # Invalid: > 180
                status='present',
                is_within_radius=True,
            )
        
        assert 'ck_att_lon_range' in str(exc_info.value)

    def test_is_late_method(self, sample_student, sample_session):
        """Test is_late() model method."""
        att_late = Attendance.objects.create(
            student_profile=sample_student,
            session=sample_session,
            latitude=Decimal('-1.28334000'),
            longitude=Decimal('36.81667000'),
            status='late',
            is_within_radius=False,
        )
        
        assert att_late.is_late() is True
        assert att_late.is_present() is False

    def test_is_present_method(self, sample_student, sample_session):
        """Test is_present() model method."""
        att_present = Attendance.objects.create(
            student_profile=sample_student,
            session=sample_session,
            latitude=Decimal('-1.28334000'),
            longitude=Decimal('36.81667000'),
            status='present',
            is_within_radius=True,
        )
        
        assert att_present.is_present() is True
        assert att_present.is_late() is False

    def test_get_distance_from_session(self, sample_student, sample_session):
        """Test get_distance_from_session() calculates distance using Haversine."""
        # Create attendance ~50m away from session location
        # Session at (-1.28333412, 36.81666588)
        # Attendance at (-1.28380000, 36.81700000) - approximately 50-60m away
        attendance = Attendance.objects.create(
            student_profile=sample_student,
            session=sample_session,
            latitude=Decimal('-1.28380000'),
            longitude=Decimal('36.81700000'),
            status='late',
            is_within_radius=False,
        )
        
        distance = attendance.get_distance_from_session()
        
        # Distance should be approximately 50-60 meters
        assert 45 <= distance <= 65
        assert isinstance(distance, float)

    def test_get_distance_from_session_same_location(self, sample_student, sample_session):
        """Test distance calculation when at same location (0 meters)."""
        attendance = Attendance.objects.create(
            student_profile=sample_student,
            session=sample_session,
            latitude=sample_session.latitude,
            longitude=sample_session.longitude,
            status='present',
            is_within_radius=True,
        )
        
        distance = attendance.get_distance_from_session()
        
        # Distance should be very close to 0 (floating-point precision)
        assert distance < 0.1

    def test_was_on_time_method_early(self, sample_student):
        """Test was_on_time() returns True when marked in first half of session."""
        # Create session with 2-hour duration
        from attendance_recording.tests.conftest import create_test_session
        session = create_test_session(
            time_created=timezone.now() - timedelta(minutes=30),  # Started 30 min ago
            time_ended=timezone.now() + timedelta(minutes=90),    # Ends in 90 min (2hr total)
            latitude=Decimal('-1.28333412'),
            longitude=Decimal('36.81666588'),
        )
        
        # Mark attendance 30 minutes into session (first half)
        attendance = Attendance.objects.create(
            student_profile=sample_student,
            session=session,
            latitude=Decimal('-1.28334000'),
            longitude=Decimal('36.81667000'),
            status='present',
            is_within_radius=True,
        )
        
        assert attendance.was_on_time() is True

    def test_was_on_time_method_late(self, sample_student):
        """Test was_on_time() returns False when marked in second half of session."""
        # Create session with 2-hour duration
        from attendance_recording.tests.conftest import create_test_session
        session = create_test_session(
            time_created=timezone.now() - timedelta(minutes=90),  # Started 90 min ago
            time_ended=timezone.now() + timedelta(minutes=30),    # Ends in 30 min (2hr total)
            latitude=Decimal('-1.28333412'),
            longitude=Decimal('36.81666588'),
        )
        
        # Mark attendance 90 minutes into session (second half)
        attendance = Attendance.objects.create(
            student_profile=sample_student,
            session=session,
            latitude=Decimal('-1.28334000'),
            longitude=Decimal('36.81667000'),
            status='late',
            is_within_radius=True,
        )
        
        assert attendance.was_on_time() is False

    def test_time_recorded_auto_now(self, sample_student, sample_session):
        """Verify auto-set timestamp is within 1 second of current time."""
        before = timezone.now()
        
        attendance = Attendance.objects.create(
            student_profile=sample_student,
            session=sample_session,
            latitude=Decimal('-1.28334000'),
            longitude=Decimal('36.81667000'),
            status='present',
            is_within_radius=True,
        )
        
        after = timezone.now()
        
        assert before <= attendance.time_recorded <= after
        time_diff = (attendance.time_recorded - before).total_seconds()
        assert time_diff < 1.0
