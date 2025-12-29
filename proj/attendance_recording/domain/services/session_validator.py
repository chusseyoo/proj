"""Session validation service."""
from __future__ import annotations
from datetime import datetime
from ..value_objects.coordinates import SessionTimeWindow
from ..exceptions import SessionNotActiveError, StudentNotEligibleError


class SessionValidator:
    """Validates session activity window and student eligibility.
    
    Business Rules:
    - Session must be active (current time within start/end window)
    - Student program must match session program
    - If session has stream requirement, student stream must match
    """

    @staticmethod
    def validate_session_is_active(time_window: SessionTimeWindow, current_time: datetime | None = None) -> None:
        """Validate that session is currently active.
        
        Args:
            time_window: Session's time window (start and end times)
            current_time: Current datetime (defaults to now if not provided)
        
        Raises:
            SessionNotActiveError: If session is not active
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Check if session has ended
        if time_window.is_ended(current_time):
            raise SessionNotActiveError("Session has ended")
        
        # Check if session has not started
        if not time_window.is_started(current_time):
            raise SessionNotActiveError("Session has not started yet")

    @staticmethod
    def validate_student_eligibility(
        *,
        student_program_id: str,
        session_program_id: str,
        student_stream: str | None = None,
        session_stream: str | None = None,
        student_is_active: bool | None = True,
    ) -> None:
        """Validate that student is eligible for this session.
        
        Eligibility Rules:
        1. Student's program must match session's program
        2. If session has stream requirement, student's stream must match
        
        Args:
            student_program_id: Student's enrolled program ID
            session_program_id: Session's target program ID
            student_stream: Student's stream (if applicable)
            session_stream: Session's stream requirement (if applicable)
            student_is_active: Whether the student account is active
        
        Raises:
            StudentNotEligibleError: If program or stream don't match
        """
        # Rule 0: Student must be active
        if student_is_active is False:
            raise StudentNotEligibleError("Student account is inactive")

        # Rule 1: Program must match
        if student_program_id != session_program_id:
            raise StudentNotEligibleError(
                f"Student program '{student_program_id}' does not match "
                f"session program '{session_program_id}'"
            )
        
        # Rule 2: If session has stream, student stream must match
        if session_stream is not None:
            if student_stream is None:
                raise StudentNotEligibleError(
                    f"Session requires stream '{session_stream}', "
                    f"but student has no stream assigned"
                )
            if student_stream != session_stream:
                raise StudentNotEligibleError(
                    f"Student stream '{student_stream}' does not match "
                    f"session stream '{session_stream}'"
                )
