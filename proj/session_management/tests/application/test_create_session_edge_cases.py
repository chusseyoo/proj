from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from session_management.application.factory import build_inmemory_container, build_app_usecases
from session_management.application.commands_builders import build_create_session_command
from session_management.application.commands_builders import CommandValidationError
from session_management.domain.exceptions.core import LecturerNotAssignedError, StreamMismatchError


def make_payload(start: datetime, end: datetime, **overrides):
    base = {
        "program_id": 1,
        "course_id": 10,
        "stream_id": None,
        "time_created": start.isoformat(),
        "time_ended": end.isoformat(),
        "latitude": "51.5",
        "longitude": "-0.1",
        "location_description": "Room",
    }
    base.update(overrides)
    return base


def test_builder_rejects_too_short_duration():
    now = datetime.now(timezone.utc)
    start = now + timedelta(minutes=5)
    end = start + timedelta(minutes=10)  # shorter than MIN_DURATION (30m)

    payload = make_payload(start, end)
    with pytest.raises(CommandValidationError):
        build_create_session_command(payload)


def test_builder_rejects_invalid_coordinates():
    now = datetime.now(timezone.utc)
    start = now + timedelta(minutes=10)
    end = start + timedelta(minutes=45)

    payload = make_payload(start, end, latitude="not-a-lat", longitude="not-a-lon")
    with pytest.raises(CommandValidationError):
        build_create_session_command(payload)


def test_create_fails_when_lecturer_inactive():
    # Build container where course 10 is assigned to lecturer 42 but lecturer is inactive
    # provide a non-empty active_lecturers set that does NOT include 42 to simulate inactive
    container = build_inmemory_container(course_lecturer_map={10: 42}, active_lecturers={999})
    create_uc = container["create"]

    now = datetime.now(timezone.utc)
    start = now + timedelta(minutes=10)
    end = start + timedelta(minutes=45)
    payload = make_payload(start, end)

    with pytest.raises(LecturerNotAssignedError):
        create_uc.execute(auth_lecturer_id=42, payload=payload)


def test_create_fails_on_stream_course_mismatch():
    # Build a custom academic port that reports course not belonging to program

    class BadAcademicPort:
        def program_has_streams(self, program_id: int) -> bool:
            return False

        def stream_belongs_to_program(self, stream_id: int, program_id: int) -> bool:
            return False

        def course_belongs_to_program(self, course_id: int, program_id: int) -> bool:
            return False

        def get_course_lecturer(self, course_id: int) -> int:
            return 42

    repo = container_repo = build_inmemory_container()["repo"]
    users = build_inmemory_container()["users"]
    bad_acad = BadAcademicPort()

    usecases = build_app_usecases(repository=repo, academic_port=bad_acad, user_port=users, publisher=None)
    create_uc = usecases["create"]

    now = datetime.now(timezone.utc)
    start = now + timedelta(minutes=10)
    end = start + timedelta(minutes=45)
    payload = make_payload(start, end)

    with pytest.raises(StreamMismatchError):
        create_uc.execute(auth_lecturer_id=42, payload=payload)


def test_create_allows_retroactive_session():
    # start in the past but within allowed duration
    container = build_inmemory_container(course_lecturer_map={10: 1}, active_lecturers={1})
    create_uc = container["create"]

    now = datetime.now(timezone.utc)
    start = now - timedelta(minutes=10)  # already started 10 minutes ago
    end = start + timedelta(minutes=45)
    payload = make_payload(start, end)

    created = create_uc.execute(auth_lecturer_id=1, payload=payload)
    assert created["session_id"] is not None
