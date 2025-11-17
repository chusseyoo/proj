from datetime import datetime, timedelta, timezone, date
from unittest.mock import Mock

import pytest

from session_management.domain.value_objects.time_window import TimeWindow
from session_management.domain.value_objects.location import Location
from session_management.domain.entities.session import Session
from session_management.domain.services.session_rules import SessionService
from session_management.domain.exceptions import (
    OverlappingSessionError,
    LecturerNotAssignedError,
    StreamMismatchError,
)


def make_sample_session():
    now = datetime.now(timezone.utc)
    tw = TimeWindow(start=now, end=now + timedelta(minutes=30))
    loc = Location(latitude=1.0, longitude=1.0)
    return Session(
        session_id=None,
        program_id=1,
        course_id=2,
        lecturer_id=3,
        stream_id=None,
        date_created=date.today(),
        time_window=tw,
        location=loc,
    )


def test_service_creates_when_no_overlap():
    repo = Mock()
    repo.has_overlapping.return_value = False
    academic = Mock()
    academic.course_belongs_to_program.return_value = True
    academic.program_has_streams.return_value = True
    academic.stream_belongs_to_program.return_value = True
    academic.get_course_lecturer.return_value = 3
    users = Mock()
    users.is_lecturer_active.return_value = True
    sample = make_sample_session()
    # saved is an immutable domain entity with an id assigned by persistence
    saved = Session(
        session_id=10,
        program_id=sample.program_id,
        course_id=sample.course_id,
        lecturer_id=sample.lecturer_id,
        stream_id=sample.stream_id,
        date_created=sample.date_created,
        time_window=sample.time_window,
        location=sample.location,
    )
    repo.save.return_value = saved

    svc = SessionService(repo, academic, users)
    out = svc.create_session(sample)
    assert out.session_id == 10
    repo.has_overlapping.assert_called_once()
    repo.save.assert_called_once_with(sample)


def test_service_raises_on_overlap():
    repo = Mock()
    repo.has_overlapping.return_value = True
    sample = make_sample_session()
    academic = Mock()
    users = Mock()
    svc = SessionService(repo, academic, users)
    with pytest.raises(OverlappingSessionError):
        svc.create_session(sample)


def test_service_raises_when_lecturer_not_assigned():
    repo = Mock()
    repo.has_overlapping.return_value = False
    academic = Mock()
    academic.course_belongs_to_program.return_value = True
    academic.program_has_streams.return_value = True
    academic.get_course_lecturer.return_value = 999  # different
    users = Mock()
    users.is_lecturer_active.return_value = True

    sample = make_sample_session()
    svc = SessionService(repo, academic, users)
    with pytest.raises(LecturerNotAssignedError):
        svc.create_session(sample)


def test_service_raises_when_stream_mismatch():
    repo = Mock()
    repo.has_overlapping.return_value = False
    academic = Mock()
    academic.course_belongs_to_program.return_value = True
    academic.program_has_streams.return_value = False
    users = Mock()
    users.is_lecturer_active.return_value = True

    sample = make_sample_session()
    # set a stream to simulate mismatch
    sample_with_stream = Session(
        session_id=None,
        program_id=sample.program_id,
        course_id=sample.course_id,
        lecturer_id=sample.lecturer_id,
        stream_id=123,
        date_created=sample.date_created,
        time_window=sample.time_window,
        location=sample.location,
    )

    svc = SessionService(repo, academic, users)
    with pytest.raises(StreamMismatchError):
        svc.create_session(sample_with_stream)
