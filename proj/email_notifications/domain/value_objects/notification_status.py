"""Value objects for email notifications context."""
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from email_notifications.domain.exceptions import (
    InvalidEmailAddressError,
    InvalidNotificationStatusError,
    InvalidTokenExpiryError,
)


class NotificationStatus(str, Enum):
    """Email notification delivery status."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    
    @classmethod
    def validate(cls, value: str) -> None:
        """Validate status is one of allowed values.
        
        Args:
            value: Status string to validate
            
        Raises:
            InvalidNotificationStatusError: Status not in allowed values
        """
        if value not in [status.value for status in cls]:
            raise InvalidNotificationStatusError(
                f"Invalid status '{value}'. Must be one of: {', '.join(s.value for s in cls)}"
            )
    
    def can_transition_to(self, next_status: "NotificationStatus") -> bool:
        """Check if transition to next status is allowed.
        
        Rules:
        - pending → sent: ✅ Allowed
        - pending → failed: ✅ Allowed
        - sent → any: ❌ NOT allowed (sent is final)
        - failed → pending: ✅ Allowed (retry)
        
        Args:
            next_status: Target status
            
        Returns:
            True if transition allowed, False otherwise
        """
        if self == NotificationStatus.SENT:
            # Once sent, cannot transition
            return False
        
        return True


@dataclass(frozen=True)
class EmailAddress:
    """Immutable email address value object with validation."""
    
    address: str
    
    def __post_init__(self) -> None:
        """Validate email format."""
        if not self.address or not isinstance(self.address, str):
            raise InvalidEmailAddressError("Email address must be non-empty string")
        
        # Basic email validation (RFC 5322 simplified)
        if "@" not in self.address or "." not in self.address:
            raise InvalidEmailAddressError(f"Invalid email address format: {self.address}")
        
        local, domain = self.address.rsplit("@", 1)
        
        if not local or not domain:
            raise InvalidEmailAddressError(f"Invalid email address format: {self.address}")
        
        if len(self.address) > 254:
            raise InvalidEmailAddressError("Email address too long (max 254 chars)")
    
    def __str__(self) -> str:
        """Return email address as string."""
        return self.address


@dataclass(frozen=True)
class TokenExpiryTime:
    """Immutable token expiry timestamp with validation."""
    
    expires_at: datetime  # Unix timestamp or datetime with timezone
    
    def __post_init__(self) -> None:
        """Validate expiry is in the future."""
        now = datetime.now(timezone.utc)
        
        # Handle both datetime and unix timestamp
        if isinstance(self.expires_at, (int, float)):
            expires_dt = datetime.fromtimestamp(self.expires_at, tz=timezone.utc)
        else:
            expires_dt = self.expires_at
        
        if expires_dt <= now:
            raise InvalidTokenExpiryError(
                f"Token expiry must be in future, got {expires_dt} (now: {now})"
            )
    
    def is_expired(self, check_time: datetime = None) -> bool:
        """Check if token is expired at given time.
        
        Args:
            check_time: Time to check against (default: now)
            
        Returns:
            True if expired, False otherwise
        """
        if check_time is None:
            check_time = datetime.now(timezone.utc)
        
        if isinstance(self.expires_at, (int, float)):
            expires_dt = datetime.fromtimestamp(self.expires_at, tz=timezone.utc)
        else:
            expires_dt = self.expires_at
        
        return check_time >= expires_dt


@dataclass(frozen=True)
class StudentID:
    """Immutable student profile ID value object."""
    
    value: int
    
    def __post_init__(self) -> None:
        """Validate student ID is positive integer."""
        if not isinstance(self.value, int) or self.value <= 0:
            raise ValueError("Student ID must be positive integer")
    
    def __int__(self) -> int:
        """Allow conversion to int."""
        return self.value


@dataclass(frozen=True)
class SessionID:
    """Immutable session ID value object."""
    
    value: int
    
    def __post_init__(self) -> None:
        """Validate session ID is positive integer."""
        if not isinstance(self.value, int) or self.value <= 0:
            raise ValueError("Session ID must be positive integer")
    
    def __int__(self) -> int:
        """Allow conversion to int."""
        return self.value
