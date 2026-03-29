"""Celery tasks for asynchronous email notification workflows."""

from __future__ import annotations

from typing import Any, Dict

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from email_notifications.application.use_cases.generate_notifications import (
    GenerateNotificationsForSession,
)
from email_notifications.domain.services.email_sender_service import EmailSenderService
from email_notifications.domain.services.jwt_service import JWTTokenService
from email_notifications.domain.services.notification_generation_service import (
    NotificationGenerationService,
)
from email_notifications.infrastructure.repositories.email_repository import (
    EmailNotificationRepository,
)
from session_management.infrastructure.repositories.session_repository import SessionRepository
from user_management.infrastructure.repositories.student_profile_repository import (
    StudentProfileRepository,
)
from user_management.infrastructure.repositories.user_repository import UserRepository


def _session_provider(session_id: int) -> Dict[str, Any] | None:
    repo = SessionRepository()
    try:
        session = repo.get_by_id(session_id)
    except Exception:
        return None

    if not session:
        return None

    return {
        "session_id": session.session_id,
        "start_time": session.time_window.start,
        "program_id": session.program_id,
        "stream_id": session.stream_id,
    }


def _students_provider(session_info: Dict[str, Any]) -> list[Dict[str, Any]]:
    student_repo = StudentProfileRepository()
    user_repo = UserRepository()

    program_id = session_info.get("program_id")
    stream_id = session_info.get("stream_id")

    if stream_id:
        students = student_repo.list_by_stream(stream_id)
    else:
        students = student_repo.list_by_program(program_id)

    eligible = []
    for student in students:
        user = user_repo.find_by_id(student.user_id)
        if not user:
            continue
        email = str(user.email).strip()
        if not email:
            continue
        eligible.append(
            {
                "student_profile_id": student.student_profile_id,
                "user_email": email,
            }
        )

    return eligible


def _build_email_context(notification) -> Dict[str, Any]:
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


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def generate_notifications_for_session_task(self, session_id: int) -> Dict[str, Any]:
    """Generate pending notifications for all eligible students in a session."""
    notification_service = NotificationGenerationService(
        jwt_service=JWTTokenService(secret_key=getattr(settings, "SECRET_KEY", "test-secret")),
        token_expiry_minutes=30,
    )

    use_case = GenerateNotificationsForSession(
        session_provider=_session_provider,
        students_provider=_students_provider,
        notification_service=notification_service,
        notification_repository=EmailNotificationRepository(),
    )

    result = use_case.execute(session_id)

    # Kick off delivery in background after creation completes.
    if result.get("notifications_created", 0) > 0:
        send_pending_notifications_task.delay(limit=100)

    return result


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def send_pending_notifications_task(self, limit: int = 100) -> Dict[str, Any]:
    """Dispatch pending email notifications and update delivery status."""
    repo = EmailNotificationRepository()
    sender = EmailSenderService()

    pending = list(
        repo.get_pending_emails(limit=max(1, int(limit))).select_related(
            "session__course",
            "student_profile__user",
        )
    )

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

            was_sent = sender.send_attendance_notification(
                recipient_email=recipient_email,
                context=_build_email_context(notification),
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
        except Exception:
            try:
                repo.update_status(
                    email_id=notification.email_id,
                    new_status=notification.Status.FAILED,
                )
            except Exception:
                pass
            failed_count += 1

    return {
        "processed": len(pending),
        "sent": sent_count,
        "failed": failed_count,
    }
