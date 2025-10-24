"""Unit tests for AttendanceAggregator (domain layer)."""
from datetime import datetime, timedelta

from reporting.domain.services.attendance_aggregator import AttendanceAggregator
from reporting.application.dto.report_dto import StudentRowDTO


class SimpleSession:
    def __init__(self, start_time: datetime, end_time: datetime):
        self.start_time = start_time
        self.end_time = end_time


def test_present_in_window_and_radius():
    agg = AttendanceAggregator()
    start = datetime(2025, 10, 19, 8, 0, 0)
    end = datetime(2025, 10, 19, 10, 0, 0)
    session = SimpleSession(start, end)

    students = [{"student_id": "s1", "student_name": "Alice"}]
    attendance = [
        {
            "student_id": "s1",
            "time_recorded": start + timedelta(minutes=5),
            "within_radius": True,
            "latitude": "1.0",
            "longitude": "2.0",
            "status": "present",
        }
    ]

    rows = agg.classify(session, students, attendance)
    assert len(rows) == 1
    r = rows[0]
    assert isinstance(r, StudentRowDTO)
    assert r.status == "Present"
    assert r.within_radius is True


def test_absent_no_attendance():
    agg = AttendanceAggregator()
    start = datetime(2025, 10, 19, 8, 0, 0)
    end = datetime(2025, 10, 19, 10, 0, 0)
    session = SimpleSession(start, end)

    students = [{"student_id": "s2", "student_name": "Bob"}]
    attendance = []

    rows = agg.classify(session, students, attendance)
    assert rows[0].status == "Absent"
    assert rows[0].time_recorded is None


def test_absent_outside_radius():
    agg = AttendanceAggregator()
    start = datetime(2025, 10, 19, 8, 0, 0)
    end = datetime(2025, 10, 19, 10, 0, 0)
    session = SimpleSession(start, end)

    students = [{"student_id": "s3", "student_name": "Cara"}]
    attendance = [
        {
            "student_id": "s3",
            "time_recorded": start + timedelta(minutes=15),
            "within_radius": False,
            "latitude": "0.0",
            "longitude": "0.0",
            "status": "present",
        }
    ]

    rows = agg.classify(session, students, attendance)
    assert rows[0].status == "Absent"
    assert rows[0].within_radius is False
    assert rows[0].time_recorded is not None


def test_boundary_times_inclusive():
    agg = AttendanceAggregator()
    start = datetime(2025, 10, 19, 8, 0, 0)
    end = datetime(2025, 10, 19, 10, 0, 0)
    session = SimpleSession(start, end)

    students = [
        {"student_id": "s4", "student_name": "Dan"},
        {"student_id": "s5", "student_name": "Eve"},
    ]
    attendance = [
        {"student_id": "s4", "time_recorded": start, "within_radius": True, "latitude": "0", "longitude": "0", "status": "present"},
        {"student_id": "s5", "time_recorded": end, "within_radius": True, "latitude": "0", "longitude": "0", "status": "present"},
    ]

    rows = agg.classify(session, students, attendance)
    assert {r.student_id: r.status for r in rows} == {"s4": "Present", "s5": "Present"}


def test_multiple_records_preference_for_qualifying():
    agg = AttendanceAggregator()
    start = datetime(2025, 10, 19, 8, 0, 0)
    end = datetime(2025, 10, 19, 10, 0, 0)
    session = SimpleSession(start, end)

    students = [{"student_id": "s6", "student_name": "Fay"}]
    attendance = [
        {"student_id": "s6", "time_recorded": start + timedelta(minutes=1), "within_radius": False, "latitude": "0", "longitude": "0", "status": "present"},
        {"student_id": "s6", "time_recorded": start + timedelta(minutes=2), "within_radius": True, "latitude": "9", "longitude": "9", "status": "present"},
    ]

    rows = agg.classify(session, students, attendance)
    r = rows[0]
    assert r.status == "Present"
    # diagnostics should prefer the qualifying record (within_radius True)
    assert r.latitude == "9"
