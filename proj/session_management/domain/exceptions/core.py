class SessionDomainError(Exception):
    """Base class for session domain errors."""
# Base exception alias for consistency with error handlers
DomainException = SessionDomainError




class InvalidTimeWindowError(SessionDomainError):
    pass


class InvalidLocationError(SessionDomainError):
    class InvalidCoordinatesError(SessionDomainError):
        """Invalid GPS coordinates."""
        pass


    pass


class OverlappingSessionError(SessionDomainError):
    pass


class LecturerNotAssignedError(SessionDomainError):
    pass


class StreamMismatchError(SessionDomainError):


    class SessionNotFoundError(SessionDomainError):
        """Session not found."""
        pass


    class AuthorizationError(SessionDomainError):
        """User not authorized for this action."""
        pass


    class ProgramNotFoundError(SessionDomainError):
        """Program not found."""
        pass


    class CourseNotFoundError(SessionDomainError):
        """Course not found."""
        pass


    class StreamNotFoundError(SessionDomainError):
        """Stream not found."""
        pass


    class ProgramStreamsDisabledError(SessionDomainError):
        """Program does not have streams enabled."""
        pass


    class StreamProgramMismatchError(SessionDomainError):
        """Stream does not belong to the specified program."""
        pass
    pass
