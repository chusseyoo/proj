"""Application DTOs for email notifications."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

from email_notifications.domain.entities import EmailNotification


@dataclass
class EmailNotificationDTO:
    """Data transfer object for EmailNotification.

    DTO intentionally excludes JWT token; enriches with user info when provided.
    """

    email_id: int
    session_id: int
    student_profile_id: int
    student_name: Optional[str]
    student_email: Optional[str]
    token_expires_at: datetime
    status: str
    created_at: datetime
    sent_at: Optional[datetime]

    @staticmethod
    def from_entity(
        notification: EmailNotification,
        student_name: Optional[str] = None,
        student_email: Optional[str] = None,
    ) -> "EmailNotificationDTO":
        """Map domain entity to DTO with optional user enrichment."""
        return EmailNotificationDTO(
            email_id=notification.email_id or 0,
            session_id=int(notification.session_id.value),
            student_profile_id=int(notification.student_id.value),
            student_name=student_name,
            student_email=student_email,
            token_expires_at=notification.token_expires_at.expires_at,
            status=notification.status.value,
            created_at=notification.created_at,
            sent_at=notification.sent_at,
        )

    def to_dict(self) -> dict:
        """Serialize DTO to primitive dict for JSON responses."""
        return {
            "email_id": self.email_id,
            "session_id": self.session_id,
            "student_profile_id": self.student_profile_id,
            "student_name": self.student_name,
            "student_email": self.student_email,
            "token_expires_at": self.token_expires_at,
            "status": self.status,
            "created_at": self.created_at,
            "sent_at": self.sent_at,
        }
