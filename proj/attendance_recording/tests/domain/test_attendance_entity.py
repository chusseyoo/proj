import pytest
from datetime import datetime

from attendance_recording.domain.entities.attendance import Attendance


class TestAttendanceEntity:
    def test_create_success(self):
        attendance = Attendance.create(
            student_id=1,
            session_id=2,
            time_recorded=datetime.now(),
            latitude=0.0,
            longitude=0.0,
            status="present",
            is_within_radius=True,
        )
        assert attendance.attendance_id is None
        assert attendance.status == "present"
        assert attendance.is_within_radius is True

    @pytest.mark.parametrize("lat", [-91, 91])
    def test_invalid_latitude(self, lat):
        with pytest.raises(ValueError):
            Attendance.create(
                student_id=1,
                session_id=2,
                time_recorded=datetime.now(),
                latitude=lat,
                longitude=0.0,
                status="present",
                is_within_radius=True,
            )

    @pytest.mark.parametrize("status", ["absent", "on_time", "LATE"])
    def test_invalid_status(self, status):
        with pytest.raises(ValueError):
            Attendance.create(
                student_id=1,
                session_id=2,
                time_recorded=datetime.now(),
                latitude=0.0,
                longitude=0.0,
                status=status,
                is_within_radius=True,
            )

    def test_negative_student_id(self):
        with pytest.raises(ValueError):
            Attendance.create(
                student_id=-5,
                session_id=2,
                time_recorded=datetime.now(),
                latitude=0.0,
                longitude=0.0,
                status="present",
                is_within_radius=True,
            )
