"""Exception handler for Email Notifications context.

Maps domain errors to DRF responses, following the shared error envelope.
"""

from rest_framework.response import Response
from rest_framework import status

from email_notifications.domain.exceptions import (
    SessionNotFoundError,
    NotificationNotFoundError,
    InvalidNotificationStatusError,
    InvalidTokenError,
    ExpiredTokenError,
    TokenGenerationError,
    EmailDeliveryError,
)


def _error(code: str, message: str, details: dict | None = None, http_status: int = status.HTTP_400_BAD_REQUEST):
    return Response(
        {
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
        status=http_status,
    )


def custom_exception_handler(exc, context):
    """Map known domain exceptions to JSON responses. Return None to defer."""
    if isinstance(exc, SessionNotFoundError):
        return _error("SessionNotFoundError", str(exc), http_status=status.HTTP_404_NOT_FOUND)
    if isinstance(exc, NotificationNotFoundError):
        return _error("NotificationNotFoundError", str(exc), http_status=status.HTTP_404_NOT_FOUND)
    if isinstance(exc, InvalidNotificationStatusError):
        return _error("InvalidNotificationStatusError", str(exc), http_status=status.HTTP_400_BAD_REQUEST)
    if isinstance(exc, (InvalidTokenError, ExpiredTokenError)):
        return _error(type(exc).__name__, str(exc), http_status=status.HTTP_400_BAD_REQUEST)
    if isinstance(exc, (TokenGenerationError, EmailDeliveryError)):
        return _error(type(exc).__name__, str(exc), http_status=status.HTTP_502_BAD_GATEWAY)

    # Defer to global handler
    return None
