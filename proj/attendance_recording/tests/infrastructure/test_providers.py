"""Tests for infrastructure persistence providers.

Validates:
- Session provider fetches correct data across contexts
- Student provider fetches correct data across contexts
- Proper handling of missing data (DoesNotExist cases)
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

from attendance_recording.infrastructure.persistence.session_provider import get_session_info
from attendance_recording.infrastructure.persistence.student_provider import get_student_info
from user_management.models import User, StudentProfile
from session_management.models import Session


@pytest.mark.django_db
class TestSessionProvider:
    """Test session provider adapter for cross-context data access."""

    def test_get_session_info_success(self, sample_session):
        """Retrieve session details with all required fields."""
        result = get_session_info(sample_session.session_id)
        
        assert result is not None
        assert 'latitude' in result
        assert 'longitude' in result
        assert 'start_time' in result
        assert 'end_time' in result
        assert 'program_id' in result
        assert 'stream_id' in result
        
        assert isinstance(result['latitude'], float)
        assert isinstance(result['longitude'], float)
        assert result['start_time'] == sample_session.time_created
        assert result['end_time'] == sample_session.time_ended

    def test_get_session_info_not_found(self):
        """Returns empty dict when session doesn't exist."""
        result = get_session_info(99999)
        
        assert result == {}

    def test_get_session_info_coordinates_conversion(self):
        """Verify Decimal coordinates converted to float."""
        from attendance_recording.tests.conftest import create_test_session
        session = create_test_session(
            time_created=timezone.now(),
            time_ended=timezone.now() + timedelta(hours=2),
            latitude=Decimal('-1.28333412'),
            longitude=Decimal('36.81666588'),
        )
        
        result = get_session_info(session.session_id)
        
        assert isinstance(result['latitude'], float)
        assert isinstance(result['longitude'], float)
        assert abs(result['latitude'] - (-1.28333412)) < 0.00000001
        assert abs(result['longitude'] - 36.81666588) < 0.00000001


@pytest.mark.django_db
class TestStudentProvider:
    """Test student provider adapter for cross-context data access."""

    def test_get_student_info_success(self, sample_student):
        """Retrieve student details with all required fields."""
        result = get_student_info(sample_student.student_profile_id)
        
        assert result is not None
        assert 'student_profile_id' in result
        assert 'program_id' in result
        assert 'stream_id' in result
        assert 'is_active' in result
        assert 'student_id' in result
        
        assert result['student_profile_id'] == sample_student.student_profile_id
        assert result['student_id'] == sample_student.student_id
        assert isinstance(result['is_active'], bool)

    def test_get_student_info_not_found(self):
        """Returns empty dict when student doesn't exist."""
        result = get_student_info(99999)
        
        assert result == {}

    def test_get_student_info_active_flag(self):
        """Verify is_active flag reflects user.is_active status."""
        # Create active student
        from attendance_recording.tests.conftest import create_test_user, create_test_student_profile
        user_active = create_test_user(
            email='active@test.com',
            first_name='Active',
            last_name='Student',
        )
        user_active.is_active = True
        user_active.save()
        
        student_active = create_test_student_profile(user_active, student_id='BCS/234300')
        
        result_active = get_student_info(student_active.student_profile_id)
        assert result_active['is_active'] is True
        
        # Create inactive student
        user_inactive = create_test_user(
            email='inactive@test.com',
            first_name='Inactive',
            last_name='Student',
        )
        user_inactive.is_active = False
        user_inactive.save()
        
        student_inactive = create_test_student_profile(user_inactive, student_id='BCS/234301')
        
        result_inactive = get_student_info(student_inactive.student_profile_id)
        assert result_inactive['is_active'] is False

    def test_get_student_info_student_id_format(self, sample_student):
        """Verify student_id field contains correct format (e.g., BCS/234344)."""
        result = get_student_info(sample_student.student_profile_id)
        
        assert 'student_id' in result
        assert '/' in result['student_id']  # Should be format like "BCS/234344"
        assert result['student_id'] == sample_student.student_id
