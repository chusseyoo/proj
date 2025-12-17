"""Application use case: generate notifications for a session."""
from datetime import datetime
from typing import Callable, List, Dict, Any

from email_notifications.domain.exceptions import SessionNotFoundError
from email_notifications.domain.services.notification_generation_service import (
    NotificationGenerationService,
)
from email_notifications.infrastructure.repositories.email_repository import (
    EmailNotificationRepository,
)


class GenerateNotificationsForSession:
    """Generate notifications for all eligible students of a session.

    This orchestrates cross-context lookups (session + eligible students) and
    delegates token creation to the domain NotificationGenerationService.
    """

    def __init__(
        self,
        session_provider: Callable[[int], Dict[str, Any]],
        students_provider: Callable[[Dict[str, Any]], List[Dict[str, Any]]],
        notification_service: NotificationGenerationService,
        notification_repository: EmailNotificationRepository = EmailNotificationRepository,
    ) -> None:
        self.session_provider = session_provider
        self.students_provider = students_provider
        self.notification_service = notification_service
        self.notification_repository = notification_repository

    def execute(self, session_id: int) -> Dict[str, Any]:
        """Run the workflow and persist notifications.

        Returns summary dict with session_id, notifications_created, eligible_students.
        """
        session = self.session_provider(session_id)
        if not session:
            raise SessionNotFoundError(f"Session with id {session_id} does not exist")

        session_start: datetime = session.get("start_time") or session.get("session_start_time")
        if session_start is None:
            raise ValueError("Session start time required for token expiry calculation")

        eligible_students = self.students_provider(session)

        generated = self.notification_service.generate_notifications_for_session(
            session_id=session_id,
            session_start_time=session_start,
            eligible_students=eligible_students,
        )

        notifications = generated.get("notifications", [])
        if not notifications:
            return {
                "session_id": session_id,
                "notifications_created": 0,
                "eligible_students": len(eligible_students),
            }

        payloads = [
            {
                "session_id": int(n.session_id.value),
                "student_profile_id": int(n.student_id.value),
                "token": n.token,
                "token_expires_at": n.token_expires_at.expires_at,
                "status": n.status.value,
            }
            for n in notifications
        ]

        created = self.notification_repository.bulk_create(payloads)

        return {
            "session_id": session_id,
            "notifications_created": len(created),
            "eligible_students": len(eligible_students),
        }
