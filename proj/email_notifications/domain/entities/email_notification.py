"""EmailNotification domain entity."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from email_notifications.domain.value_objects.notification_status import (
    NotificationStatus,
    StudentID,
    SessionID,
    TokenExpiryTime,
)
from email_notifications.domain.exceptions import (
    InvalidNotificationStatusError,
)


@dataclass(frozen=True)
class EmailNotification:
    """Domain entity representing an email notification.

    Immutable aggregate root for email notification.
    One notification = one email to one student for one session.

    Attributes:
        email_id: Unique identifier (None until persisted)
        session_id: Session this email is for
        student_id: Student receiving the email
        token: JWT token embedded in attendance link
        token_expires_at: Token expiration timestamp
        status: Delivery status (pending/sent/failed)
        created_at: When notification was created
        sent_at: When email was successfully sent (nullable)
    """
    
    session_id: SessionID
    student_id: StudentID
    token: str
    token_expires_at: TokenExpiryTime
    status: NotificationStatus
    created_at: datetime
    email_id: Optional[int] = None
    sent_at: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        """Validate entity invariants."""
        # Validate token is non-empty
        if not self.token or not isinstance(self.token, str):
            raise ValueError("Token must be non-empty string")
        
        # Validate status
        try:
            NotificationStatus.validate(self.status.value)
        except Exception as e:
            raise InvalidNotificationStatusError(str(e))
        
        # Validate created_at is timezone-aware
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must have timezone information")
        
        # Validate sent_at constraints
        if self.sent_at is not None:
            if self.sent_at.tzinfo is None:
                raise ValueError("sent_at must have timezone information if set")
            
            # sent_at only allowed when status is sent
            if self.status != NotificationStatus.SENT:
                raise InvalidNotificationStatusError(
                    f"sent_at must be NULL when status is {self.status}, got {self.sent_at}"
                )
            
            # sent_at must be after created_at
            if self.sent_at < self.created_at:
                raise ValueError("sent_at must be after created_at")
        else:
            # sent_at must be NULL when status is pending or failed
            if self.status == NotificationStatus.SENT:
                raise InvalidNotificationStatusError(
                    "sent_at must be set when status is sent"
                )
    
    def is_expired(self) -> bool:
        """Check if token has expired.
        
        Returns:
            True if token expired, False otherwise
        """
        return self.token_expires_at.is_expired()
    
    def is_sent(self) -> bool:
        """Check if notification was successfully sent.
        
        Returns:
            True if status is sent, False otherwise
        """
        return self.status == NotificationStatus.SENT
    
    def can_retry(self) -> bool:
        """Check if notification can be retried.
        
        Notifications can be retried if status is failed.
        
        Returns:
            True if status is failed, False otherwise
        """
        return self.status == NotificationStatus.FAILED
    
    def mark_as_sent(self, sent_timestamp: datetime = None) -> "EmailNotification":
        """Create new notification with sent status.
        
        Returns a new instance (immutable pattern) with:
        - status set to SENT
        - sent_at set to current time (or provided timestamp)
        
        Args:
            sent_timestamp: When email was sent (default: now)
            
        Returns:
            New EmailNotification with status=SENT
            
        Raises:
            InvalidNotificationStatusError: If current status is not pending
        """
        if self.status != NotificationStatus.PENDING:
            raise InvalidNotificationStatusError(
                f"Can only mark sent from pending status, current: {self.status}"
            )
        
        if sent_timestamp is None:
            sent_timestamp = datetime.now(timezone.utc)
        
        # Return new instance with updated fields
        return EmailNotification(
            email_id=self.email_id,
            session_id=self.session_id,
            student_id=self.student_id,
            token=self.token,
            token_expires_at=self.token_expires_at,
            status=NotificationStatus.SENT,
            created_at=self.created_at,
            sent_at=sent_timestamp,
        )
    
    def mark_as_failed(self) -> "EmailNotification":
        """Create new notification with failed status.
        
        Returns a new instance (immutable pattern) with:
        - status set to FAILED
        - sent_at set to NULL
        
        Returns:
            New EmailNotification with status=FAILED
            
        Raises:
            InvalidNotificationStatusError: If current status is sent
        """
        if self.status == NotificationStatus.SENT:
            raise InvalidNotificationStatusError(
                "Cannot mark as failed once sent"
            )
        
        return EmailNotification(
            email_id=self.email_id,
            session_id=self.session_id,
            student_id=self.student_id,
            token=self.token,
            token_expires_at=self.token_expires_at,
            status=NotificationStatus.FAILED,
            created_at=self.created_at,
            sent_at=None,
        )
    
    def mark_for_retry(self) -> "EmailNotification":
        """Create new notification reset to pending for retry.
        
        Used by admin to retry failed notifications.
        Returns a new instance with:
        - status set to PENDING
        - sent_at set to NULL
        
        Returns:
            New EmailNotification with status=PENDING
            
        Raises:
            InvalidNotificationStatusError: If current status is sent
        """
        if self.status == NotificationStatus.SENT:
            raise InvalidNotificationStatusError(
                "Cannot retry once sent"
            )
        
        return EmailNotification(
            email_id=self.email_id,
            session_id=self.session_id,
            student_id=self.student_id,
            token=self.token,
            token_expires_at=self.token_expires_at,
            status=NotificationStatus.PENDING,
            created_at=self.created_at,
            sent_at=None,
        )
