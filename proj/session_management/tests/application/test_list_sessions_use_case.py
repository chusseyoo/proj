from datetime import datetime, timedelta, timezone

from session_management.application.use_cases.list_sessions import ListMySessionsUseCase
from session_management.domain.entities.session import Session as DomainSession
from session_management.domain.value_objects.time_window import TimeWindow
from session_management.domain.value_objects.location import Location


def make_session(session_id, program_id, course_id, lecturer_id, start):
    tw = TimeWindow(start=start, end=start + timedelta(minutes=45))
    loc = Location(latitude=1.0, longitude=1.0)
    return DomainSession(
        session_id=session_id,
        program_id=program_id,
        course_id=course_id,
        lecturer_id=lecturer_id,
        stream_id=None,
        date_created=tw.start.date(),
        time_window=tw,
        location=loc,
    )


def test_list_my_sessions_filters_and_pagination():
    now = datetime.now(timezone.utc)
    sessions = [
        make_session(1, 1, 10, 3, now - timedelta(days=1)),
        make_session(2, 2, 20, 3, now - timedelta(hours=1)),
        make_session(3, 1, 30, 3, now - timedelta(minutes=30)),
    ]

    class Repo:
        def list_by_lecturer(self, lecturer_id, start=None, end=None):
            assert lecturer_id == 3
            return sessions

    use_case = ListMySessionsUseCase(Repo())

    # No filters, default page_size 20
    out = use_case.execute(3)
    assert out["total_count"] == 3

    # Filter by program_id
    out2 = use_case.execute(3, program_id=1)
    assert out2["total_count"] == 2

    # Pagination page_size=1
    out3 = use_case.execute(3, page=1, page_size=1)
    assert out3["total_pages"] == 3
    assert len(out3["results"]) == 1
