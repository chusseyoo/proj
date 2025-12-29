"""Exports for domain exceptions."""
from .core import (
    AttendanceRecordingException,
    InvalidTokenError,
    TokenInvalidError,
    TokenExpiredError,
    QRMismatchError,
    SessionNotActiveError,
    StudentNotEligibleError,
    InvalidCoordinatesError,
    DuplicateAttendanceError,
    OutsideRadiusWarning,
    LocationTooFarError,
)

__all__ = [
    "AttendanceRecordingException",
    "InvalidTokenError",
    "TokenInvalidError",
    "TokenExpiredError",
    "QRMismatchError",
    "SessionNotActiveError",
    "StudentNotEligibleError",
    "InvalidCoordinatesError",
    "DuplicateAttendanceError",
    "OutsideRadiusWarning",
    "LocationTooFarError",
]
