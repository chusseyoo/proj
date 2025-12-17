"""Domain layer for email notifications context.

Exports entities, value objects, exceptions, and services.
"""
from .entities import EmailNotification
from .value_objects import (
    NotificationStatus,
    EmailAddress,
    TokenExpiryTime,
    StudentID,
    SessionID,
)
from .services import (
    JWTTokenService,
    EmailSenderService,
    NotificationGenerationService,
)
from .exceptions import (
    EmailNotificationError,
    InvalidTokenError,
    ExpiredTokenError,
    InvalidTokenExpiryError,
    SessionNotFoundError,
    TokenGenerationError,
    EmailDeliveryError,
    InvalidEmailAddressError,
    DuplicateNotificationError,
    InvalidNotificationStatusError,
    NotificationNotFoundError,
)

__all__ = [
    # Entities
    "EmailNotification",
    # Value Objects
    "NotificationStatus",
    "EmailAddress",
    "TokenExpiryTime",
    "StudentID",
    "SessionID",
    # Services
    "JWTTokenService",
    "EmailSenderService",
    "NotificationGenerationService",
    # Exceptions
    "EmailNotificationError",
    "InvalidTokenError",
    "ExpiredTokenError",
    "InvalidTokenExpiryError",
    "SessionNotFoundError",
    "TokenGenerationError",
    "EmailDeliveryError",
    "InvalidEmailAddressError",
    "DuplicateNotificationError",
    "InvalidNotificationStatusError",
    "NotificationNotFoundError",
]
