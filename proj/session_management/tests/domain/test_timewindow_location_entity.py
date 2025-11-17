from datetime import datetime, timedelta, timezone

import pytest

from session_management.domain.value_objects.time_window import TimeWindow
from session_management.domain.value_objects.location import Location


def test_timewindow_validates_duration_and_order():
    start = datetime.now(timezone.utc)
    end = start + timedelta(minutes=5)  # too short
    with pytest.raises(ValueError):
        TimeWindow(start=start, end=end)

    end2 = start + timedelta(hours=1)
    tw = TimeWindow(start=start, end=end2)
    assert tw.start.tzinfo is not None
    assert tw.end > tw.start


def test_location_validates_ranges():
    with pytest.raises(ValueError):
        Location(latitude=100.0, longitude=0.0)
    with pytest.raises(ValueError):
        Location(latitude=0.0, longitude=200.0)
    loc = Location(latitude=0.0, longitude=0.0, radius_meters=50)
    assert loc.radius_meters == 50
