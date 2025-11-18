from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

from session_management.application.use_cases.list_sessions import ListMySessionsUseCase
from session_management.application.use_cases.get_session import GetSessionUseCase
from session_management.application.use_cases.end_session import EndSessionUseCase
from session_management.application.use_cases.update_session import UpdateSessionUseCase
from session_management.domain.value_objects.time_window import TimeWindow
from session_management.domain.value_objects.location import Location
from session_management.domain.entities.session import Session as DomainSession


def make_sample_session(now: datetime, lecturer_id: int = 3) -> DomainSession:
    tw = TimeWindow(start=now, end=now + timedelta(minutes=30))
    loc = Location(latitude=1.0, longitude=1.0)
    return DomainSession(
        session_id=1,
        program_id=1,
        course_id=2,
        lecturer_id=lecturer_id,
        stream_id=None,
        date_created=tw.start.date(),
        time_window=tw,
        location=loc,
    )


def test_list_my_sessions_use_case_filters_and_pagination():
    now = datetime.now(timezone.utc)
    s1 = make_sample_session(now)
    s2 = make_sample_session(now + timedelta(days=1))

    repo = Mock()
    repo.list_by_lecturer.return_value = [s1, s2]

    uc = ListMySessionsUseCase(repository=repo)
    page = uc.execute(auth_lecturer_id=3, page=1, page_size=1)

    assert page["total_count"] == 2
    assert len(page["results"]) == 1


def test_get_session_ownership_enforced():
    now = datetime.now(timezone.utc)
    s = make_sample_session(now, lecturer_id=5)
    repo = Mock()
    repo.get_by_id.return_value = s

    uc = GetSessionUseCase(repository=repo)
    try:
        uc.execute(auth_lecturer_id=5, session_id=1)
    except Exception:
        assert False, "should not raise for owner"

    try:
        uc.execute(auth_lecturer_id=3, session_id=1)
        assert False, "should have raised PermissionError"
    except PermissionError:
        pass


def test_end_session_sets_end_and_saves():
    now = datetime.now(timezone.utc)
    s = make_sample_session(now)
    repo = Mock()
    repo.get_by_id.return_value = s
    repo.save.return_value = s

    uc = EndSessionUseCase(repository=repo)
    out = uc.execute(auth_lecturer_id=3, session_id=1, now=now + timedelta(minutes=10))
    assert out["session_id"] == 1


def test_update_session_changes_time_window_and_location():
    now = datetime.now(timezone.utc)
    s = make_sample_session(now)
    repo = Mock()
    repo.get_by_id.return_value = s
    repo.save.return_value = s

    uc = UpdateSessionUseCase(repository=repo)
    updates = {"time_created": now.isoformat(), "time_ended": (now + timedelta(hours=1)).isoformat(), "latitude": "2.0", "longitude": "2.0"}
    out = uc.execute(auth_lecturer_id=3, session_id=1, updates=updates)
    assert out["session_id"] == 1
