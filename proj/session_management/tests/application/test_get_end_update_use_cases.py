from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from session_management.application.use_cases.get_session import GetSessionUseCase
from session_management.application.use_cases.end_session import EndSessionUseCase
from session_management.application.use_cases.update_session import UpdateSessionUseCase
from session_management.domain.entities.session import Session as DomainSession
from session_management.domain.value_objects.time_window import TimeWindow, MIN_DURATION
from session_management.domain.value_objects.location import Location


def make_session(session_id=1, lecturer_id=3, start=None):
    if start is None:
        start = datetime.now(timezone.utc)
    tw = TimeWindow(start=start, end=start + timedelta(minutes=45))
    loc = Location(latitude=1.0, longitude=1.0, description="R")
    return DomainSession(
        session_id=session_id,
        program_id=1,
        course_id=2,
        lecturer_id=lecturer_id,
        stream_id=None,
        date_created=tw.start.date(),
        time_window=tw,
        location=loc,
    )


def test_get_session_owner_ok_and_forbidden():
    s = make_session()

    class Repo:
        def get_by_id(self, session_id):
            return s

    use_case = GetSessionUseCase(Repo())
    dto = use_case.execute(auth_lecturer_id=3, session_id=1)
    assert dto["session_id"] == 1

    with pytest.raises(PermissionError):
        use_case.execute(auth_lecturer_id=99, session_id=1)


def test_end_session_sets_new_end_and_saves():
    start = datetime.now(timezone.utc)
    session = make_session(start=start)

    # Now is before min_end to force min_end usage
    now = start + timedelta(minutes=5)

    class Repo:
        def get_by_id(self, session_id):
            return session

        def save(self, new_session):
            # return object that the use-case expects
            return new_session

    use_case = EndSessionUseCase(Repo())
    dto = use_case.execute(auth_lecturer_id=3, session_id=1, now=now)

    # new end should be at least start + MIN_DURATION
    expected_end = start + MIN_DURATION
    assert dto["time_ended"] == expected_end.isoformat()


def test_update_session_changes_time_and_location_and_enforces_owner():
    start = datetime.now(timezone.utc)
    session = make_session(start=start)

    class Repo:
        def get_by_id(self, session_id):
            return session

        def save(self, new_session):
            return new_session

    use_case = UpdateSessionUseCase(Repo())

    new_start = start + timedelta(hours=1)
    new_end = new_start + timedelta(minutes=45)
    updates = {
        "time_created": new_start.isoformat().replace("+00:00", "Z"),
        "time_ended": new_end.isoformat().replace("+00:00", "Z"),
        "latitude": "2.5",
        "longitude": "3.5",
        "location_description": "New Room",
    }

    dto = use_case.execute(auth_lecturer_id=3, session_id=1, updates=updates)
    assert dto["time_created"] == new_start.isoformat()
    assert dto["time_ended"] == new_end.isoformat()
    assert dto["latitude"] == "2.5"

    # ownership enforcement
    with pytest.raises(PermissionError):
        use_case.execute(auth_lecturer_id=999, session_id=1, updates=updates)
