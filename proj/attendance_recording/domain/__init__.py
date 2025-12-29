"""Attendance recording domain layer exports."""
from .entities import Attendance
from .value_objects import StudentProfileID, SessionTimeWindow, GPSCoordinate
from .services import (
    AttendanceService,
    LocationValidator,
    QRCodeValidator,
    SessionValidator,
    TokenValidator,
    DuplicateAttendancePolicy,
)
from .exceptions import (
    AttendanceRecordingException,
    InvalidTokenError,
    TokenExpiredError,
    QRMismatchError,
    SessionNotActiveError,
    StudentNotEligibleError,
    InvalidCoordinatesError,
    DuplicateAttendanceError,
)

__all__ = [
    # Entities
    "Attendance",
    # Value Objects
    "StudentProfileID",
    "SessionTimeWindow",
    "GPSCoordinate",
    # Services
    "AttendanceService",
    "LocationValidator",
    "QRCodeValidator",
    "SessionValidator",
    "TokenValidator",
    "DuplicateAttendancePolicy",
    # Exceptions
    "AttendanceRecordingException",
    "InvalidTokenError",
    "TokenExpiredError",
    "QRMismatchError",
    "SessionNotActiveError",
    "StudentNotEligibleError",
    "InvalidCoordinatesError",
    "DuplicateAttendanceError",
]


