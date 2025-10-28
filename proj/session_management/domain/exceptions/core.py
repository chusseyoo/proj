class SessionDomainError(Exception):
    """Base class for session domain errors."""


class InvalidTimeWindowError(SessionDomainError):
    pass


class InvalidLocationError(SessionDomainError):
    pass


class OverlappingSessionError(SessionDomainError):
    pass


class LecturerNotAssignedError(SessionDomainError):
    pass


class StreamMismatchError(SessionDomainError):
    pass
