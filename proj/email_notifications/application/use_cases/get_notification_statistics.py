"""Application query: notification delivery statistics."""
from typing import Optional, Dict, Any

from email_notifications.infrastructure.repositories.email_repository import (
    EmailNotificationRepository,
)


class GetNotificationStatistics:
    """Return delivery statistics for all notifications or a session."""

    def __init__(
        self,
        notification_repository: EmailNotificationRepository = EmailNotificationRepository,
    ) -> None:
        self.notification_repository = notification_repository

    def execute(self, session_id: Optional[int] = None) -> Dict[str, Any]:
        return self.notification_repository.get_delivery_statistics(session_id=session_id)
