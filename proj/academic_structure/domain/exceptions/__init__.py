"""Domain exceptions for academic_structure."""

from .core import (
    DomainError,
    ValidationError,
    NotFoundError,
    ProgramNotFoundError,
    ProgramCodeAlreadyExistsError,
    ProgramCannotBeDeletedError,
    StreamNotFoundError,
    StreamAlreadyExistsError,
    StreamNotAllowedError,
    StreamCannotBeDeletedError,
    CourseNotFoundError,
    CourseCodeAlreadyExistsError,
    CourseCannotBeDeletedError,
    LecturerNotFoundError,
    LecturerInactiveError,
    InvalidYearError,
    InvalidDepartmentNameError,
)

__all__ = [
    "DomainError",
    "ValidationError",
    "NotFoundError",
    "ProgramNotFoundError",
    "ProgramCodeAlreadyExistsError",
    "ProgramCannotBeDeletedError",
    "StreamNotFoundError",
    "StreamAlreadyExistsError",
    "StreamNotAllowedError",
    "StreamCannotBeDeletedError",
    "CourseNotFoundError",
    "CourseCodeAlreadyExistsError",
    "CourseCannotBeDeletedError",
    "LecturerNotFoundError",
    "LecturerInactiveError",
    "InvalidYearError",
    "InvalidDepartmentNameError",
]

