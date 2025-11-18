from __future__ import annotations

# Ensure the package root is on sys.path when pytest runs this file directly.
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from datetime import datetime, timedelta, timezone

from session_management.application.in_memory_adapters import (
    InMemorySessionRepository,
    InMemoryEventPublisher,
    InMemoryAcademicPort,
    InMemoryUserPort,
)
from session_management.application.use_cases.create_session import CreateSessionUseCase
from session_management.application.use_cases.list_sessions import ListMySessionsUseCase
from session_management.application.use_cases.get_session import GetSessionUseCase
from session_management.domain.services.session_rules import SessionService


def test_create_list_get_integration_flow():
    repo = InMemorySessionRepository()
    publisher = InMemoryEventPublisher()
    academic = InMemoryAcademicPort(course_lecturer_map={10: 42})
    users = InMemoryUserPort(active_lecturers={42})

    service = SessionService(repository=repo, academic_port=academic, user_port=users)

    create_uc = CreateSessionUseCase(repository=repo, service=service, publisher=publisher)
    list_uc = ListMySessionsUseCase(repository=repo)
    get_uc = GetSessionUseCase(repository=repo)

    now = datetime.now(timezone.utc)
    start = now + timedelta(minutes=5)
    end = start + timedelta(minutes=45)

    payload = {
        "program_id": 1,
        "course_id": 10,
        "stream_id": None,
        "time_created": start.isoformat(),
        "time_ended": end.isoformat(),
        "latitude": "51.5",
        "longitude": "-0.1",
        "location_description": "Test room",
    }

    created = create_uc.execute(auth_lecturer_id=42, payload=payload)
    assert created["session_id"] is not None
    sid = created["session_id"]
    assert created["program_id"] == 1

    # list
    listing = list_uc.execute(42)
    assert listing["total_count"] == 1
    assert listing["results"][0]["session_id"] == sid

    # get
    got = get_uc.execute(42, sid)
    assert got["session_id"] == sid

    # publisher recorded event
    assert any(ev["name"] == "session.created" for ev in publisher.events)
