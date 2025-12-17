"""Domain exceptions for email notifications context."""


class EmailNotificationError(Exception):
    """Base exception for email notifications context."""
    pass


class InvalidTokenError(EmailNotificationError):
    """Token signature invalid, malformed, or tampered with."""
    pass


class ExpiredTokenError(EmailNotificationError):
    """Token has expired (past exp claim)."""
    pass


class InvalidTokenExpiryError(EmailNotificationError):
    """Token expiry time is invalid (e.g., in the past)."""
    pass


class SessionNotFoundError(EmailNotificationError):
    """Session does not exist."""
    pass


class TokenGenerationError(EmailNotificationError):
    """Failed to generate JWT token."""
    pass


class EmailDeliveryError(EmailNotificationError):
    """SMTP delivery failed."""
    pass


class InvalidEmailAddressError(EmailNotificationError):
    """Email address is invalid or malformed."""
    pass


class DuplicateNotificationError(EmailNotificationError):
    """Notification already exists for student-session pair."""
    pass


class InvalidNotificationStatusError(EmailNotificationError):
    """Invalid status value or illegal status transition."""
    pass


class NotificationNotFoundError(EmailNotificationError):
    """Notification does not exist."""
    pass
