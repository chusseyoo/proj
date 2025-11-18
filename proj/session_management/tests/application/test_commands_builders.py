from __future__ import annotations

from datetime import datetime, timezone, timedelta

from session_management.application.commands_builders import build_create_session_command, CommandValidationError


def test_build_create_session_command_happy_path():
    now = datetime.now(timezone.utc)
    start = now + timedelta(minutes=10)
    end = start + timedelta(minutes=45)

    payload = {
        "program_id": "1",
        "course_id": "2",
        "stream_id": None,
        "time_created": start.isoformat(),
        "time_ended": end.isoformat(),
        "latitude": "51.5",
        "longitude": "-0.1",
        "location_description": "Room 1",
    }

    cmd = build_create_session_command(payload)
    assert cmd.program_id == 1
    assert cmd.course_id == 2
    assert cmd.time_created.tzinfo is not None
    assert cmd.time_ended > cmd.time_created


def test_build_create_session_command_missing_fields():
    payload = {"program_id": 1}
    try:
        build_create_session_command(payload)
        assert False, "expected CommandValidationError"
    except CommandValidationError:
        pass


def test_build_create_session_command_bad_iso():
    payload = {
        "program_id": 1,
        "course_id": 2,
        "time_created": "not-a-date",
        "time_ended": "2020-01-01T00:30:00Z",
        "latitude": "0",
        "longitude": "0",
    }
    try:
        build_create_session_command(payload)
        assert False, "expected CommandValidationError"
    except CommandValidationError:
        pass
