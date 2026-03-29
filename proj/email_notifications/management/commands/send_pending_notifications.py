"""Dispatch pending email notifications.

Usage:
    python manage.py send_pending_notifications
    python manage.py send_pending_notifications --limit 50
"""

from __future__ import annotations

from typing import Any, Dict

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from email_notifications.infrastructure.repositories.email_repository import (
    EmailNotificationRepository,
)
from email_notifications.domain.services.email_sender_service import EmailSenderService


class Command(BaseCommand):
    help = "Send pending email notifications and update their delivery status"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Maximum number of pending notifications to process (default: 100)",
        )

    def handle(self, *args, **options) -> None:
        limit = max(1, int(options.get("limit") or 100))

        repo = EmailNotificationRepository()
        sender = EmailSenderService()

        pending = list(repo.get_pending_emails(limit=limit).select_related("session__course", "student_profile__user"))
        if not pending:
            self.stdout.write(self.style.SUCCESS("No pending notifications found."))
            return

        sent_count = 0
        failed_count = 0

        for notification in pending:
            try:
                recipient_email = (notification.student_profile.user.email or "").strip()
                if not recipient_email:
                    repo.update_status(
                        email_id=notification.email_id,
                        new_status=notification.Status.FAILED,
                    )
                    failed_count += 1
                    continue

                context = self._build_email_context(notification)

                was_sent = sender.send_attendance_notification(
                    recipient_email=recipient_email,
                    context=context,
                )

                if was_sent:
                    repo.update_status(
                        email_id=notification.email_id,
                        new_status=notification.Status.SENT,
                        sent_at=timezone.now(),
                    )
                    sent_count += 1
                else:
                    repo.update_status(
                        email_id=notification.email_id,
                        new_status=notification.Status.FAILED,
                    )
                    failed_count += 1
            except Exception as exc:  # pragma: no cover - defensive
                try:
                    repo.update_status(
                        email_id=notification.email_id,
                        new_status=notification.Status.FAILED,
                    )
                except Exception:
                    pass
                failed_count += 1
                self.stderr.write(
                    self.style.WARNING(
                        f"Notification {notification.email_id} failed: {exc}"
                    )
                )

        total = len(pending)
        self.stdout.write(
            self.style.SUCCESS(
                f"Processed {total} pending notifications: sent={sent_count}, failed={failed_count}."
            )
        )

    def _build_email_context(self, notification) -> Dict[str, Any]:
        session = notification.session
        student_user = notification.student_profile.user

        attendance_base_url = getattr(
            settings,
            "ATTENDANCE_MARK_BASE_URL",
            "http://localhost:8000/student/scan",
        )
        attendance_link = f"{attendance_base_url}?token={notification.token}"

        return {
            "student_first_name": student_user.first_name or "Student",
            "course_name": getattr(session.course, "course_name", "Attendance Session"),
            "course_code": getattr(session.course, "course_code", "N/A"),
            "session_date": str(session.time_created.date()),
            "start_time": session.time_created.strftime("%H:%M"),
            "end_time": session.time_ended.strftime("%H:%M"),
            "attendance_link": attendance_link,
            "token_expiry": notification.token_expires_at.isoformat(),
        }
