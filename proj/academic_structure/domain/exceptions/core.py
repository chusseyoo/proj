"""Core domain exceptions for academic_structure context."""


class DomainError(Exception):
    """Base class for domain-level exceptions in academic_structure."""


class ValidationError(DomainError, ValueError):
    """Raised when a value object or entity validation fails."""


class NotFoundError(DomainError):
    """Raised when an expected domain object cannot be found."""


# Program exceptions
class ProgramNotFoundError(NotFoundError):
    """Raised when a program is not found."""


class ProgramCodeAlreadyExistsError(DomainError):
    """Raised when attempting to create a program with duplicate code."""


class ProgramCannotBeDeletedError(DomainError):
    """Raised when attempting to delete a program with students or courses."""


# Stream exceptions
class StreamNotFoundError(NotFoundError):
    """Raised when a stream is not found."""


class StreamAlreadyExistsError(DomainError):
    """Raised when attempting to create a duplicate stream."""


class StreamNotAllowedError(DomainError):
    """Raised when attempting to create a stream for program without has_streams=True."""


class StreamCannotBeDeletedError(DomainError):
    """Raised when attempting to delete a stream with assigned students."""


# Course exceptions
class CourseNotFoundError(NotFoundError):
    """Raised when a course is not found."""


class CourseCodeAlreadyExistsError(DomainError):
    """Raised when attempting to create a course with duplicate code."""


class CourseCannotBeDeletedError(DomainError):
    """Raised when attempting to delete a course with existing sessions."""


# Cross-context exceptions (User Management)
class LecturerNotFoundError(NotFoundError):
    """Raised when a lecturer is not found."""


class LecturerInactiveError(DomainError):
    """Raised when attempting to assign an inactive lecturer to a course."""


# Validation exceptions
class InvalidYearError(ValidationError):
    """Raised when year of study is out of valid range (1-4)."""


class InvalidDepartmentNameError(ValidationError):
    """Raised when department name doesn't meet validation requirements."""
