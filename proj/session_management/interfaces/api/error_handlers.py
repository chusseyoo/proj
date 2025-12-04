"""Error handling and domain exception mapping for Session Management API."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from ...domain.exceptions.core import (
    DomainException,
    InvalidTimeWindowError,
    InvalidLocationError,
    OverlappingSessionError,
)
from ...application.exceptions import (
    CommandValidationError,
)


# Map domain exceptions to HTTP status codes
DOMAIN_EXCEPTION_STATUS_MAP = {
    'InvalidTimeWindowError': status.HTTP_400_BAD_REQUEST,
    'InvalidLocationError': status.HTTP_400_BAD_REQUEST,
    'OverlappingSessionError': status.HTTP_409_CONFLICT,
    'ProgramNotFoundError': status.HTTP_404_NOT_FOUND,
    'CourseNotFoundError': status.HTTP_404_NOT_FOUND,
    'StreamNotFoundError': status.HTTP_404_NOT_FOUND,
    'SessionNotFoundError': status.HTTP_404_NOT_FOUND,
    'ProgramStreamsDisabledError': status.HTTP_400_BAD_REQUEST,
    'StreamProgramMismatchError': status.HTTP_400_BAD_REQUEST,
    'AuthorizationError': status.HTTP_403_FORBIDDEN,
    'CommandValidationError': status.HTTP_400_BAD_REQUEST,
}


def get_error_code(exception):
    """Get error code from exception."""
    if hasattr(exception, '__class__'):
        return exception.__class__.__name__
    return 'UnknownError'


def format_error_response(error_code: str, message: str) -> dict:
    """Format error response according to API spec."""
    return {
        "error": {
            "code": error_code,
            "message": message
        }
    }


def custom_exception_handler(exc, context):
    """
    Custom exception handler that maps domain exceptions to proper HTTP responses.
    Falls back to DRF's default handler for non-domain exceptions.
    """
    # Handle domain exceptions
    if isinstance(exc, (DomainException, CommandValidationError)):
        error_code = get_error_code(exc)
        message = str(exc)
        http_status = DOMAIN_EXCEPTION_STATUS_MAP.get(error_code, status.HTTP_400_BAD_REQUEST)
        
        return Response(
            format_error_response(error_code, message),
            status=http_status
        )
    
    # Handle validation errors from serializers
    response = drf_exception_handler(exc, context)
    
    if response is not None:
        # Reformat DRF validation errors to match our error format
        if isinstance(response.data, dict) and not response.data.get('error'):
            # Convert DRF error format to our format
            error_message = "Validation error"
            if 'detail' in response.data:
                error_message = response.data['detail']
            elif response.data:
                # Combine all field errors
                errors = []
                for field, messages in response.data.items():
                    if isinstance(messages, list):
                        errors.append(f"{field}: {', '.join(messages)}")
                    else:
                        errors.append(f"{field}: {messages}")
                error_message = "; ".join(errors)
            
            response.data = format_error_response("ValidationError", error_message)
    
    return response


def handle_use_case_exception(func):
    """
    Decorator to handle exceptions from use cases and convert them to HTTP responses.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (DomainException, CommandValidationError) as e:
            error_code = get_error_code(e)
            http_status = DOMAIN_EXCEPTION_STATUS_MAP.get(error_code, status.HTTP_400_BAD_REQUEST)
            return Response(
                format_error_response(error_code, str(e)),
                status=http_status
            )
        except Exception as e:
            # Unexpected error
            return Response(
                format_error_response("InternalServerError", "An unexpected error occurred"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return wrapper
