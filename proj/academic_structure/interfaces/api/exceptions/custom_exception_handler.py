"""
Custom exception handler for academic_structure context.
Maps domain exceptions to HTTP status codes and error responses.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from ....domain.exceptions import (
    ProgramNotFoundError,
    CourseNotFoundError,
    StreamNotFoundError,
    StreamAlreadyExistsError,
    InvalidYearError,
    InvalidDepartmentNameError,
)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        if isinstance(exc, NotAuthenticated):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            response['WWW-Authenticate'] = 'Bearer realm="api"'
        elif isinstance(exc, PermissionDenied):
            response.status_code = status.HTTP_403_FORBIDDEN
    if response is None:
        response = handle_domain_exception(exc)
    return response

def handle_domain_exception(exc):
    if isinstance(exc, (ProgramNotFoundError, CourseNotFoundError, StreamNotFoundError)):
        return Response({'error': str(exc)}, status=status.HTTP_404_NOT_FOUND)
    if isinstance(exc, StreamAlreadyExistsError):
        return Response({'error': str(exc)}, status=status.HTTP_409_CONFLICT)
    if isinstance(exc, (InvalidYearError, InvalidDepartmentNameError)):
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return None
