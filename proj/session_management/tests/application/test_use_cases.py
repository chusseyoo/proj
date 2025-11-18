from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from session_management.application.use_cases.create_session import CreateSessionUseCase
from session_management.application.use_cases.list_sessions import ListMySessionsUseCase
from session_management.application.use_cases.get_session import GetSessionUseCase
from session_management.application.use_cases.end_session import EndSessionUseCase
from session_management.application.use_cases.update_session import UpdateSessionUseCase


def make_sample_domain_session():
    from session_management.domain.value_objects.time_window import TimeWindow
    from session_management.domain.value_objects.location import Location
    from session_management.domain.entities.session import Session

    now = datetime.now(timezone.utc)
    tw = TimeWindow(start=now, end=now + timedelta(minutes=30))
    loc = Location(latitude=1.0, longitude=2.0)
    return Session(
        session_id=1,
        program_id=1,
        course_id=2,
        lecturer_id=3,
        stream_id=None,
        date_created=now.date(),
        time_window=tw,
        location=loc,
    )


def test_create_session_use_case_calls_service_and_publishes():
    repo = Mock()
    svc = Mock()
    publisher = Mock()

    sample = make_sample_domain_session()
    svc.create_session.return_value = sample

    uc = CreateSessionUseCase(repository=repo, service=svc, publisher=publisher)

    payload = {
        "program_id": 1,
        "course_id": 2,
        "time_created": sample.time_window.start.isoformat(),
        "time_ended": sample.time_window.end.isoformat(),
        "latitude": sample.location.latitude,
        "longitude": sample.location.longitude,
    }

    out = uc.execute(auth_lecturer_id=3, payload=payload)
    assert out["session_id"] == sample.session_id
    svc.create_session.assert_called_once()
    publisher.publish.assert_called_once()


def test_list_get_update_end_basic_flow():
    # repository returns the sample in list_by_lecturer and get_by_id
    repo = Mock()
    sample = make_sample_domain_session()
    repo.list_by_lecturer.return_value = [sample]
    repo.get_by_id.return_value = sample
    repo.save.return_value = sample

    list_uc = ListMySessionsUseCase(repository=repo)
    page = list_uc.execute(auth_lecturer_id=3)
    assert page["total_count"] == 1

    get_uc = GetSessionUseCase(repository=repo)
    got = get_uc.execute(auth_lecturer_id=3, session_id=1)
    assert got["session_id"] == sample.session_id

    end_uc = EndSessionUseCase(repository=repo)
    ended = end_uc.execute(auth_lecturer_id=3, session_id=1)
    assert ended["session_id"] == sample.session_id

    update_uc = UpdateSessionUseCase(repository=repo)
    updated = update_uc.execute(auth_lecturer_id=3, session_id=1, updates={})
    assert updated["session_id"] == sample.session_id
