"""
Repositories for user management infrastructure.
"""

from .user_repository import UserRepository
from .student_profile_repository import StudentProfileRepository
from .lecturer_profile_repository import LecturerProfileRepository

__all__ = [
    'UserRepository',
    'StudentProfileRepository',
    'LecturerProfileRepository',
]
