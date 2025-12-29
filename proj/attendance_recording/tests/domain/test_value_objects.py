import pytest
from datetime import datetime

from attendance_recording.domain import (
    StudentProfileID,
    SessionTimeWindow,
    GPSCoordinate,
)


class TestStudentProfileID:
    def test_positive_int_ok(self):
        sid = StudentProfileID(123)
        assert int(sid) == 123

    @pytest.mark.parametrize("bad", [0, -1, "abc", 1.5])
    def test_invalid_values_raise(self, bad):
        with pytest.raises(ValueError):
            StudentProfileID(bad)


class TestGPSCoordinate:
    def test_valid_coordinates(self):
        coord = GPSCoordinate(-1.28333412, 36.81666588)
        assert coord.to_dict() == {
            "latitude": -1.28333412,
            "longitude": 36.81666588,
        }

    @pytest.mark.parametrize("lat, lon", [(-91, 0), (91, 0)])
    def test_invalid_latitude_raises(self, lat, lon):
        with pytest.raises(ValueError):
            GPSCoordinate(lat, lon)

    @pytest.mark.parametrize("lat, lon", [(0, -181), (0, 181)])
    def test_invalid_longitude_raises(self, lat, lon):
        with pytest.raises(ValueError):
            GPSCoordinate(lat, lon)


class TestSessionTimeWindow:
    def test_valid_window(self):
        start = datetime(2025, 10, 25, 8, 0)
        end = datetime(2025, 10, 25, 10, 0)
        window = SessionTimeWindow(start_time=start, end_time=end)
        assert window.is_active(start)
        assert window.is_started(start)
        assert window.is_ended(end) is False

    def test_end_before_start_raises(self):
        start = datetime(2025, 10, 25, 10, 0)
        end = datetime(2025, 10, 25, 8, 0)
        with pytest.raises(ValueError):
            SessionTimeWindow(start_time=start, end_time=end)
