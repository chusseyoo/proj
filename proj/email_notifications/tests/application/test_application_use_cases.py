"""Application layer use case tests (unit, mocked dependencies)."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import List

import pytest

from email_notifications.application.use_cases.generate_notifications import (
    GenerateNotificationsForSession,
)
from email_notifications.application.use_cases.retry_failed_notifications import (
    RetryFailedNotifications,
)
from email_notifications.application.use_cases.list_notifications import (
    ListNotificationsForSession,
)
from email_notifications.application.use_cases.get_notification_statistics import (
    GetNotificationStatistics,
)
from email_notifications.domain.services.notification_generation_service import (
    NotificationGenerationService,
)
from email_notifications.domain.services.jwt_service import JWTTokenService
from email_notifications.domain.value_objects import NotificationStatus


@pytest.fixture
def now():
    return datetime.now(timezone.utc)


class FakeRepo:
    def __init__(self):
        self.created: List[dict] = []
        self.items: List[SimpleNamespace] = []
        self.updated = []

    # generate notifications
    def bulk_create(self, payloads):
        self.created.extend(payloads)
        # return a fake model with email_id set
        return [SimpleNamespace(email_id=i + 1, **p) for i, p in enumerate(payloads)]

    # retry
    def get_by_id(self, email_id):
        for it in self.items:
            if it.email_id == email_id:
                return it
        raise ValueError("not found")

    def update_status(self, email_id, new_status, sent_at=None):
        self.updated.append((email_id, new_status, sent_at))
        return SimpleNamespace(email_id=email_id, status=new_status, sent_at=sent_at)

    # list
    def get_by_session(self, session_id):
        class QS(list):
            def filter(self, **kwargs):
                if "status" in kwargs:
                    return QS([i for i in self if i.status == kwargs["status"]])
                return self

            def count(self):
                return len(self)

        return QS([i for i in self.items if i.session_id == session_id])

    # stats
    def get_delivery_statistics(self, session_id=None):
        return {"total": 1, "sent": 1, "failed": 0, "pending": 0, "success_rate": 100}


class FakeNotification:
    def __init__(self, session_id, student_id, token="t", created_at=None):
        self.session_id = SimpleNamespace(value=session_id)
        self.student_id = SimpleNamespace(value=student_id)
        self.token = token
        self.token_expires_at = SimpleNamespace(expires_at=datetime.now(timezone.utc) + timedelta(minutes=60))
        self.status = NotificationStatus.PENDING
        self.created_at = created_at or datetime.now(timezone.utc)
        self.sent_at = None
        self.email_id = None


def test_generate_notifications_success(now):
    session_provider = lambda session_id: {"session_id": session_id, "start_time": now}
    students_provider = lambda session: [
        {"student_profile_id": 1},
        {"student_profile_id": 2},
    ]

    jwt_service = JWTTokenService(secret_key="secret")
    notification_service = NotificationGenerationService(jwt_service=jwt_service)

    fake_repo = FakeRepo()
    # stub notifications returned by domain service
    def generate_stub(session_id, session_start_time, eligible_students):
        return {
            "session_id": session_id,
            "notifications": [
                FakeNotification(session_id=session_id, student_id=s["student_profile_id"])
                for s in eligible_students
            ],
            "count": len(eligible_students),
        }

    notification_service.generate_notifications_for_session = generate_stub  # type: ignore

    use_case = GenerateNotificationsForSession(
        session_provider=session_provider,
        students_provider=students_provider,
        notification_service=notification_service,
        notification_repository=fake_repo,
    )

    result = use_case.execute(session_id=10)

    assert result["session_id"] == 10
    assert result["notifications_created"] == 2
    assert len(fake_repo.created) == 2
    assert fake_repo.created[0]["student_profile_id"] == 1


def test_retry_failed_notifications():
    fake_repo = FakeRepo()
    failed = SimpleNamespace(email_id=1, status="failed", Status=SimpleNamespace(PENDING="pending", FAILED="failed", SENT="sent"))
    sent = SimpleNamespace(email_id=2, status="sent", Status=failed.Status)
    fake_repo.items = [failed, sent]

    use_case = RetryFailedNotifications(notification_repository=fake_repo)
    result = use_case.execute([1, 2, 3])

    assert result["retried"] == 1
    assert result["skipped"] == 1  # sent skipped
    assert len(result["errors"]) == 1  # id 3 missing
    assert fake_repo.updated[0][1] == "pending"


def test_list_notifications_with_pagination():
    fake_repo = FakeRepo()
    fake_repo.items = [
        SimpleNamespace(
            email_id=1,
            session_id=10,
            student_profile_id=5,
            token_expires_at=datetime.now(timezone.utc),
            status="pending",
            created_at=datetime.now(timezone.utc),
            sent_at=None,
        ),
        SimpleNamespace(
            email_id=2,
            session_id=10,
            student_profile_id=6,
            token_expires_at=datetime.now(timezone.utc),
            status="sent",
            created_at=datetime.now(timezone.utc),
            sent_at=datetime.now(timezone.utc),
        ),
    ]

    enricher = lambda student_profile_id: {"name": f"Student {student_profile_id}", "email": f"s{student_profile_id}@example.com"}

    use_case = ListNotificationsForSession(notification_repository=fake_repo, student_enricher=enricher)
    result = use_case.execute(session_id=10, status=None, page=1, page_size=1)

    assert result["total_count"] == 2
    assert len(result["results"]) == 1
    assert result["has_next"] is True
    assert result["results"][0]["student_name"].startswith("Student")


def test_get_notification_statistics():
    fake_repo = FakeRepo()
    use_case = GetNotificationStatistics(notification_repository=fake_repo)

    stats = use_case.execute(session_id=None)

    assert stats["success_rate"] == 100
