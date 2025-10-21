"""
Domain entities for user management.
"""

from .user import User, UserRole
from .student_profile import StudentProfile
from .lecturer_profile import LecturerProfile

__all__ = [
    'User',
    'UserRole',
    'StudentProfile',
    'LecturerProfile',
]
