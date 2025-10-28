"""Exceptions package for session_management domain.

Exports the domain exceptions for convenient imports.
"""
from .core import (
    SessionDomainError,
    InvalidTimeWindowError,
    InvalidLocationError,
    OverlappingSessionError,
    LecturerNotAssignedError,
    StreamMismatchError,
)

__all__ = [
    "SessionDomainError",
    "InvalidTimeWindowError",
    "InvalidLocationError",
    "OverlappingSessionError",
    "LecturerNotAssignedError",
    "StreamMismatchError",
]
