from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from session_management.application.use_cases.create_session import CreateSessionUseCase
from session_management.infrastructure.publishers.in_memory_publisher import InMemoryPublisher
from session_management.domain.entities.session import Session as DomainSession
from session_management.domain.value_objects.time_window import TimeWindow
from session_management.domain.value_objects.location import Location
from session_management.domain.exceptions import OverlappingSessionError


def make_saved_session(start=None):
    if start is None:
        start = datetime.now(timezone.utc)
    tw = TimeWindow(start=start, end=start + timedelta(minutes=45))
    loc = Location(latitude=1.0, longitude=1.0)
    return DomainSession(
        session_id=42,
        program_id=1,
        course_id=2,
        lecturer_id=3,
        stream_id=None,
        date_created=tw.start.date(),
        time_window=tw,
        location=loc,
    )


def test_create_session_publishes_event_and_returns_dto():
    now = datetime.now(timezone.utc)
    payload = {
        "program_id": 1,
        "course_id": 2,
        "time_created": now.isoformat().replace("+00:00", "Z"),
        "time_ended": (now + timedelta(minutes=45)).isoformat().replace("+00:00", "Z"),
        "latitude": "1.0",
        "longitude": "1.0",
        "location_description": "Room 101",
    }

    mock_repo = Mock()
    mock_service = Mock()
    saved = make_saved_session(start=now)
    mock_service.create_session.return_value = saved

    publisher = InMemoryPublisher()

    use_case = CreateSessionUseCase(mock_repo, mock_service, publisher=publisher)
    dto = use_case.execute(auth_lecturer_id=3, payload=payload)

    assert dto["session_id"] == 42
    # ensure event was published
    assert len(publisher.events) == 1
    ev = publisher.events[0]
    assert ev["event"] == "session.created"
    assert ev["payload"]["session_id"] == 42


def test_create_session_on_overlap_does_not_publish_and_raises():
    now = datetime.now(timezone.utc)
    payload = {
        "program_id": 1,
        "course_id": 2,
        "time_created": now.isoformat().replace("+00:00", "Z"),
        "time_ended": (now + timedelta(minutes=45)).isoformat().replace("+00:00", "Z"),
        "latitude": "1.0",
        "longitude": "1.0",
    }

    mock_repo = Mock()
    mock_service = Mock()
    mock_service.create_session.side_effect = OverlappingSessionError("overlap")

    publisher = InMemoryPublisher()

    use_case = CreateSessionUseCase(mock_repo, mock_service, publisher=publisher)

    with pytest.raises(OverlappingSessionError):
        use_case.execute(auth_lecturer_id=3, payload=payload)

    assert len(publisher.events) == 0
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from session_management.application.use_cases.create_session import CreateSessionUseCase
from session_management.infrastructure.publishers.in_memory_publisher import InMemoryPublisher
from session_management.domain.value_objects.time_window import TimeWindow
from session_management.domain.value_objects.location import Location
from session_management.domain.entities.session import Session as DomainSession
from session_management.domain.exceptions import OverlappingSessionError


def make_payload(now: datetime):
    return {
        "program_id": 1,
        "course_id": 2,
        "stream_id": None,
        "time_created": now.isoformat(),
        "time_ended": (now + timedelta(minutes=30)).isoformat(),
        "latitude": "1.0",
        "longitude": "1.0",
        "location_description": "Room 101",
    }


def make_sample_saved(now: datetime):
    tw = TimeWindow(start=now, end=now + timedelta(minutes=30))
    loc = Location(latitude=1.0, longitude=1.0, description="Room 101")
    return DomainSession(
        session_id=10,
        program_id=1,
        course_id=2,
        lecturer_id=3,
        stream_id=None,
        date_created=tw.start.date(),
        time_window=tw,
        location=loc,
    )


def test_create_session_happy_path():
    now = datetime.now(timezone.utc)
    payload = make_payload(now)

    repo = Mock()
    svc = Mock()
    saved = make_sample_saved(now)
    svc.create_session.return_value = saved

    pub = InMemoryPublisher()

    uc = CreateSessionUseCase(repo, svc, publisher=pub)
    out = uc.execute(auth_lecturer_id=3, payload=payload)

    assert out["session_id"] == 10
    assert len(pub.events) == 1
    assert pub.events[0]["event"] == "session.created"


def test_create_session_raises_overlap():
    now = datetime.now(timezone.utc)
    payload = make_payload(now)

    repo = Mock()
    svc = Mock()
    svc.create_session.side_effect = OverlappingSessionError()

    uc = CreateSessionUseCase(repo, svc, publisher=None)
    with pytest.raises(OverlappingSessionError):
        uc.execute(auth_lecturer_id=3, payload=payload)
