"""
Exception Handling for DRF API.

Maps domain exceptions to HTTP status codes and error responses.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

from ...domain.exceptions import (
    # User exceptions
    UserNotFoundError,
    EmailAlreadyExistsError,
    UserInactiveError,
    # Student exceptions
    StudentNotFoundError,
    StudentIdAlreadyExistsError,
    InvalidStudentIdFormatError,
    StudentCannotHavePasswordError,
    StudentCannotLoginError,
    # Lecturer exceptions
    LecturerNotFoundError,
    # Program/Stream exceptions
    ProgramNotFoundError,
    StreamRequiredError,
    StreamNotAllowedError,
    StreamNotInProgramError,
    InvalidYearError,
    InvalidDepartmentNameError,
    # Auth exceptions
    InvalidCredentialsError,
    InvalidPasswordError,
    WeakPasswordError,
    InvalidTokenError,
    ExpiredTokenError,
    InvalidTokenTypeError,
    TokenAlreadyUsedError,
    # Authorization exceptions
    UnauthorizedError,
)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that maps domain exceptions to HTTP responses.
    """
    # Call DRF's default handler first
    response = exception_handler(exc, context)
    
    # If DRF didn't handle it, try our domain exceptions
    if response is None:
        response = handle_domain_exception(exc)
    
    return response


def handle_domain_exception(exc):
    """
    Map domain exceptions to HTTP status codes and error format.
    """
    # 404 Not Found
    if isinstance(exc, (UserNotFoundError, StudentNotFoundError, LecturerNotFoundError, ProgramNotFoundError)):
        return Response(
            {'error': str(exc)},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # 409 Conflict (duplicates)
    if isinstance(exc, (EmailAlreadyExistsError, StudentIdAlreadyExistsError)):
        return Response(
            {'error': str(exc)},
            status=status.HTTP_409_CONFLICT
        )
    
    # 401 Unauthorized (auth failures)
    if isinstance(exc, (InvalidCredentialsError, InvalidPasswordError, ExpiredTokenError, InvalidTokenError, InvalidTokenTypeError)):
        return Response(
            {'error': str(exc)},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # 403 Forbidden (permission denied)
    if isinstance(exc, (UnauthorizedError, UserInactiveError, StudentCannotLoginError, StudentCannotHavePasswordError)):
        return Response(
            {'error': str(exc)},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # 400 Bad Request (validation errors)
    if isinstance(exc, (
        WeakPasswordError,
        InvalidStudentIdFormatError,
        StreamRequiredError,
        StreamNotAllowedError,
        StreamNotInProgramError,
        InvalidYearError,
        InvalidDepartmentNameError,
        TokenAlreadyUsedError,
    )):
        return Response(
            {'error': str(exc)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # If not a domain exception, return None (let DRF handle it)
    return None
