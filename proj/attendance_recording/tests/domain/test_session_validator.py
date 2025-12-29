import pytest
from datetime import datetime, timedelta

from attendance_recording.domain.services.session_validator import SessionValidator
from attendance_recording.domain.value_objects.coordinates import SessionTimeWindow
from attendance_recording.domain.exceptions import SessionNotActiveError, StudentNotEligibleError


class TestSessionValidator:
    def test_session_active_ok(self):
        now = datetime.now()
        window = SessionTimeWindow(now - timedelta(minutes=5), now + timedelta(minutes=5))
        SessionValidator.validate_session_is_active(window, current_time=now)

    def test_session_not_started_raises(self):
        now = datetime.now()
        window = SessionTimeWindow(now + timedelta(minutes=5), now + timedelta(minutes=10))
        with pytest.raises(SessionNotActiveError):
            SessionValidator.validate_session_is_active(window, current_time=now)

    def test_session_ended_raises(self):
        now = datetime.now()
        window = SessionTimeWindow(now - timedelta(minutes=10), now - timedelta(minutes=5))
        with pytest.raises(SessionNotActiveError):
            SessionValidator.validate_session_is_active(window, current_time=now)

    def test_program_mismatch_raises(self):
        with pytest.raises(StudentNotEligibleError):
            SessionValidator.validate_student_eligibility(
                student_program_id="BCS",
                session_program_id="MIT",
                student_stream=None,
                session_stream=None,
            )

    def test_stream_mismatch_raises(self):
        with pytest.raises(StudentNotEligibleError):
            SessionValidator.validate_student_eligibility(
                student_program_id="BCS",
                session_program_id="BCS",
                student_stream="A",
                session_stream="B",
            )

    def test_stream_required_missing_student_stream_raises(self):
        with pytest.raises(StudentNotEligibleError):
            SessionValidator.validate_student_eligibility(
                student_program_id="BCS",
                session_program_id="BCS",
                student_stream=None,
                session_stream="A",
            )

    def test_stream_match_ok(self):
        SessionValidator.validate_student_eligibility(
            student_program_id="BCS",
            session_program_id="BCS",
            student_stream="A",
            session_stream="A",
        )

    def test_inactive_student_raises(self):
        with pytest.raises(StudentNotEligibleError):
            SessionValidator.validate_student_eligibility(
                student_program_id="BCS",
                session_program_id="BCS",
                student_stream=None,
                session_stream=None,
                student_is_active=False,
            )
