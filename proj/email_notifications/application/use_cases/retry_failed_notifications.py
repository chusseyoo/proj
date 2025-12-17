"""Application use case: retry failed notifications."""
from typing import List, Dict, Any
from django.utils import timezone

from email_notifications.infrastructure.repositories.email_repository import (
    EmailNotificationRepository,
)


class RetryFailedNotifications:
    """Reset failed notifications to pending for retry."""

    def __init__(
        self,
        notification_repository: EmailNotificationRepository = EmailNotificationRepository,
    ) -> None:
        self.notification_repository = notification_repository

    def execute(self, email_ids: List[int]) -> Dict[str, Any]:
        """Retry failed notifications.

        Returns summary: {retried, skipped, errors}
        """
        retried = 0
        skipped = 0
        errors: List[str] = []

        for email_id in email_ids:
            try:
                notification = self.notification_repository.get_by_id(email_id)
                if notification.status == notification.Status.SENT:
                    skipped += 1
                    continue
                if notification.status != notification.Status.FAILED:
                    skipped += 1
                    continue

                self.notification_repository.update_status(
                    email_id=email_id,
                    new_status=notification.Status.PENDING,
                    sent_at=None,
                )
                retried += 1
            except Exception as exc:  # pragma: no cover - defensive
                errors.append(f"email_id={email_id}: {exc}")

        return {
            "retried": retried,
            "skipped": skipped,
            "errors": errors,
        }
