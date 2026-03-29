"""Integration test for notification generation + pending dispatcher command."""

from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from academic_structure.models import Course, Program
from email_notifications.application.use_cases.generate_notifications import (
    GenerateNotificationsForSession,
)
from email_notifications.domain.services.email_sender_service import EmailSenderService
from email_notifications.domain.services.jwt_service import JWTTokenService
from email_notifications.domain.services.notification_generation_service import (
    NotificationGenerationService,
)
from email_notifications.models import EmailNotification
from session_management.models import Session
from session_management.infrastructure.repositories.session_repository import SessionRepository
from user_management.models import LecturerProfile, StudentProfile, User
from user_management.infrastructure.repositories.student_profile_repository import (
    StudentProfileRepository,
)
from user_management.infrastructure.repositories.user_repository import UserRepository


def _create_program_course_lecturer() -> tuple[Program, Course, LecturerProfile]:
    program = Program.objects.create(
        program_name="Bachelor of Computer Science",
        program_code="BCS",
        department_name="Computer Science",
        has_streams=False,
    )

    lecturer_user = User.objects.create_user(
        email=f"lecturer_{uuid.uuid4()}@test.local",
        role="Lecturer",
        first_name="Test",
        last_name="Lecturer",
        password="TestPassword!123",
    )
    lecturer = LecturerProfile.objects.create(
        user=lecturer_user,
        department_name="Computer Science",
    )

    course = Course.objects.create(
        program=program,
        course_code="BCS012",
        course_name="Data Structures and Algorithms",
        department_name="Computer Science",
        lecturer=lecturer,
    )

    return program, course, lecturer


def _create_students(program: Program, count: int = 2) -> list[StudentProfile]:
    students: list[StudentProfile] = []

    for i in range(count):
        user = User.objects.create_user(
            email=f"student_{uuid.uuid4()}@test.local",
            role="Student",
            first_name=f"Student{i}",
            last_name="Tester",
        )
        profile = StudentProfile.objects.create(
            user=user,
            student_id=f"BCS/23432{i}",
            program=program,
            year_of_study=2,
        )
        students.append(profile)

    return students


@pytest.mark.django_db
def test_email_notification_generation_and_pending_dispatch(monkeypatch):
    """Generate pending notifications, dispatch them, and verify status transitions."""
    program, course, lecturer = _create_program_course_lecturer()
    student_profiles = _create_students(program=program, count=2)

    session = Session.objects.create(
        program=program,
        course=course,
        lecturer=lecturer,
        time_created=timezone.now() + timedelta(minutes=5),
        time_ended=timezone.now() + timedelta(hours=1),
        latitude=Decimal("-1.28333412"),
        longitude=Decimal("36.81666588"),
        location_description="Main Hall",
    )

    def session_provider(session_id: int):
        repo = SessionRepository()
        s = repo.get_by_id(session_id)
        return {
            "session_id": s.session_id,
            "start_time": s.time_window.start,
            "program_id": s.program_id,
            "stream_id": s.stream_id,
        }

    def students_provider(session_info: dict):
        student_repo = StudentProfileRepository()
        user_repo = UserRepository()

        students = student_repo.list_by_program(session_info["program_id"])
        eligible = []
        for s in students:
            user = user_repo.find_by_id(s.user_id)
            if not user:
                continue
            eligible.append(
                {
                    "student_profile_id": s.student_profile_id,
                    "user_email": str(user.email),
                }
            )
        return eligible

    generate_uc = GenerateNotificationsForSession(
        session_provider=session_provider,
        students_provider=students_provider,
        notification_service=NotificationGenerationService(
            jwt_service=JWTTokenService(secret_key="test-secret"),
            token_expiry_minutes=30,
        ),
    )

    summary = generate_uc.execute(session.session_id)
    assert summary["notifications_created"] == 2

    pending = EmailNotification.objects.filter(
        session=session,
        student_profile__in=student_profiles,
        status=EmailNotification.Status.PENDING,
    )
    assert pending.count() == 2

    monkeypatch.setattr(
        EmailSenderService,
        "send_attendance_notification",
        lambda self, recipient_email, context: True,
    )

    out = StringIO()
    call_command("send_pending_notifications", "--limit", "100", stdout=out)

    refreshed = EmailNotification.objects.filter(
        session=session,
        student_profile__in=student_profiles,
    )
    assert refreshed.filter(status=EmailNotification.Status.SENT).count() == 2
    assert refreshed.filter(status=EmailNotification.Status.PENDING).count() == 0
    assert "sent=2" in out.getvalue()
