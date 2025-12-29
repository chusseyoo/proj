"""Domain exceptions for attendance recording context.

Aligns with docs: Standard Domain Exceptions by Context (Attendance Recording)
- TokenExpiredError (410)
- TokenInvalidError (401)
- QRMismatchError (403)
- LocationTooFarError (425)
- SessionNotActiveError (410 - too early) / (425 - too late)
- DuplicateAttendanceError (409)
- StudentNotEligibleError (403)
"""


class AttendanceRecordingException(Exception):
    """Base exception for attendance recording domain."""
    pass


# Token-related exceptions
class InvalidTokenError(AttendanceRecordingException):
    """JWT token is invalid (format/signature) or cannot be decoded."""
    pass


class TokenInvalidError(InvalidTokenError):
    """Alias per docs: TokenInvalidError (recommended HTTP 401)."""
    pass


class TokenExpiredError(AttendanceRecordingException):
    """JWT token has expired based on its exp claim (recommended HTTP 410)."""
    pass


# QR code-related exceptions
class QRMismatchError(AttendanceRecordingException):
    """Scanned QR does not match expected values (recommended HTTP 403)."""
    pass


# Session-related exceptions
class SessionNotActiveError(AttendanceRecordingException):
    """Session is not active (not started or already ended).

    Docs mapping:
    - Too early: recommended HTTP 410
    - Too late: recommended HTTP 425

    The optional `phase` argument can be 'too_early' or 'too_late'.
    """

    def __init__(self, message: str = None, phase: str = None):
        self.phase = phase
        self.http_status = 410 if phase == "too_early" else (425 if phase == "too_late" else None)
        super().__init__(message or "Session is not currently active")


class StudentNotEligibleError(AttendanceRecordingException):
    """Student is not eligible for this session (recommended HTTP 403)."""
    pass


# Location-related exceptions
class InvalidCoordinatesError(AttendanceRecordingException):
    """Provided GPS coordinates are invalid or out of range."""
    pass


class OutsideRadiusWarning(AttendanceRecordingException):
    """Student is outside the allowed radius."""
    pass


class LocationTooFarError(OutsideRadiusWarning):
    """Alias per docs: LocationTooFarError (recommended HTTP 425)."""
    pass


# Attendance-related exceptions
class DuplicateAttendanceError(AttendanceRecordingException):
    """Attendance already recorded for this student-session pair (recommended HTTP 409)."""
    pass
