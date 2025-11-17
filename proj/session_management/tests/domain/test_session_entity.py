from datetime import datetime, timedelta, timezone, date

from session_management.domain.value_objects.time_window import TimeWindow
from session_management.domain.value_objects.location import Location
from session_management.domain.entities.session import Session


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


def test_session_is_active_and_has_ended_properties():
    sample = make_sample_session()
    # With the time window created above (start=now, end=now+30min) it should be active
    assert sample.is_active is True
    assert sample.has_ended is False
