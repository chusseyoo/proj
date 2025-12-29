"""Persistence adapters for attendance_recording."""

from .session_provider import get_session_info
from .student_provider import get_student_info

__all__ = ["get_session_info", "get_student_info"]