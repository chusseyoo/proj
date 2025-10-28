"""Ports package for session_management domain.

This package exposes protocol interfaces used by domain services.
"""
from .session_repository import SessionRepositoryPort
from .academic import AcademicStructurePort
from .user_management import UserManagementPort

__all__ = [
    "SessionRepositoryPort",
    "AcademicStructurePort",
    "UserManagementPort",
]
