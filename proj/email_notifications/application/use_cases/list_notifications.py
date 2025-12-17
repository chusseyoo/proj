"""Application query: list notifications for a session."""
from typing import Optional, Dict, Any, Callable

from email_notifications.application.dto import EmailNotificationDTO
from email_notifications.infrastructure.repositories.email_repository import (
    EmailNotificationRepository,
)


class ListNotificationsForSession:
    """List notifications for a session with optional status filter and pagination."""

    def __init__(
        self,
        notification_repository: EmailNotificationRepository = EmailNotificationRepository,
        student_enricher: Optional[Callable[[int], Dict[str, Any]]] = None,
    ) -> None:
        self.notification_repository = notification_repository
        self.student_enricher = student_enricher

    def execute(
        self,
        session_id: int,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        if page <= 0 or page_size <= 0:
            raise ValueError("page and page_size must be positive")

        qs = self.notification_repository.get_by_session(session_id)
        if status:
            qs = qs.filter(status=status)

        total = qs.count()
        offset = (page - 1) * page_size
        items = qs[offset : offset + page_size]

        results = []
        for notif in items:
            student_name = None
            student_email = None
            if self.student_enricher:
                enriched = self.student_enricher(notif.student_profile_id)
                if enriched:
                    student_name = enriched.get("name")
                    student_email = enriched.get("email")
            dto = EmailNotificationDTO(
                email_id=notif.email_id,
                session_id=notif.session_id,
                student_profile_id=notif.student_profile_id,
                student_name=student_name,
                student_email=student_email,
                token_expires_at=notif.token_expires_at,
                status=notif.status,
                created_at=notif.created_at,
                sent_at=notif.sent_at,
            )
            results.append(dto.to_dict())

        total_pages = (total + page_size - 1) // page_size if page_size else 1

        return {
            "results": results,
            "total_count": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
        }
