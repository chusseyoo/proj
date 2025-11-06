"""
Exception Handling for DRF API - User Management Context.

Maps domain exceptions to HTTP status codes and error responses.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from ....domain.exceptions import (
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
    # Program/Stream exceptions (user_management context)
    ProgramNotFoundError as UserMgmtProgramNotFoundError,
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
    
    Also handles proper 401 vs 403 distinction:
    - 401 Unauthorized: User is not authenticated (no credentials or invalid credentials)
    - 403 Forbidden: User is authenticated but lacks permission
    """
    # Call DRF's default handler first
    response = exception_handler(exc, context)
    
    # Handle authentication vs authorization distinction
    if response is not None:
        # Return 401 for unauthenticated requests (instead of DRF's default 403)
        if isinstance(exc, NotAuthenticated):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            # Add WWW-Authenticate header as per HTTP spec
            response['WWW-Authenticate'] = 'Bearer realm="api"'
        
        # PermissionDenied exceptions remain 403 (user is authenticated but not authorized)
        elif isinstance(exc, PermissionDenied):
            response.status_code = status.HTTP_403_FORBIDDEN
    
    # If DRF didn't handle it, try our domain exceptions
    if response is None:
        response = handle_domain_exception(exc)
    
    return response


def handle_domain_exception(exc):
    """
    Map domain exceptions to HTTP status codes and error format.
    """
    # 404 Not Found
    if isinstance(exc, (UserNotFoundError, StudentNotFoundError, LecturerNotFoundError, UserMgmtProgramNotFoundError)):
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
