"""Unit tests for AttendanceAggregator (domain layer)."""
from datetime import datetime, timedelta

from reporting.domain.services.attendance_aggregator import AttendanceAggregator
from reporting.domain.value_objects.student_attendance_row import StudentAttendanceRow


class SimpleSession:
    def __init__(self, start_time: datetime, end_time: datetime):
        self.start_time = start_time
        self.end_time = end_time


def test_present_in_window_and_radius():
    agg = AttendanceAggregator()
    start = datetime(2025, 10, 19, 8, 0, 0)
    end = datetime(2025, 10, 19, 10, 0, 0)
    session = SimpleSession(start, end)

    students = [{
        "student_id": "BCS/234344",
        "student_name": "Alice Johnson",
        "email": "alice.johnson@student.university.ac.ke",
        "program": "Computer Science",
        "stream": "Stream A"
    }]
    attendance = [
        {
            "student_id": "BCS/234344",
            "time_recorded": start + timedelta(minutes=5),
            "within_radius": True,
            "latitude": "-1.286389",
            "longitude": "36.817223",
        }
    ]

    rows = agg.classify(session, students, attendance)
    assert len(rows) == 1
    r = rows[0]
    assert isinstance(r, StudentAttendanceRow)
    assert r.status == "Present"
    assert r.within_radius is True


def test_absent_no_attendance():
    agg = AttendanceAggregator()
    start = datetime(2025, 10, 19, 8, 0, 0)
    end = datetime(2025, 10, 19, 10, 0, 0)
    session = SimpleSession(start, end)

    students = [{
        "student_id": "BCS/234345",
        "student_name": "Bob Smith",
        "email": "bob.smith@student.university.ac.ke",
        "program": "Computer Science",
        "stream": "Stream A"
    }]
    attendance = []

    rows = agg.classify(session, students, attendance)
    assert rows[0].status == "Absent"
    assert rows[0].time_recorded is None


def test_absent_outside_radius():
    agg = AttendanceAggregator()
    start = datetime(2025, 10, 19, 8, 0, 0)
    end = datetime(2025, 10, 19, 10, 0, 0)
    session = SimpleSession(start, end)

    students = [{
        "student_id": "BCS/234346",
        "student_name": "Cara Williams",
        "email": "cara.williams@student.university.ac.ke",
        "program": "Computer Science",
        "stream": "Stream B"
    }]
    attendance = [
        {
            "student_id": "BCS/234346",
            "time_recorded": start + timedelta(minutes=15),
            "within_radius": False,
            "latitude": "-1.350000",
            "longitude": "36.900000",
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
        {
            "student_id": "BIT/123456",
            "student_name": "Dan Brown",
            "email": "dan.brown@student.university.ac.ke",
            "program": "Information Technology",
            "stream": "Stream A",
        },
        {
            "student_id": "BIT/123457",
            "student_name": "Eve Davis",
            "email": "eve.davis@student.university.ac.ke",
            "program": "Information Technology",
            "stream": "Stream A",
        },
    ]
    attendance = [
        {"student_id": "BIT/123456", "time_recorded": start, "within_radius": True, "latitude": "-1.286389", "longitude": "36.817223"},
        {"student_id": "BIT/123457", "time_recorded": end, "within_radius": True, "latitude": "-1.287000", "longitude": "36.818000"},
    ]

    rows = agg.classify(session, students, attendance)
    assert {r.student_id: r.status for r in rows} == {"BIT/123456": "Present", "BIT/123457": "Present"}


def test_multiple_records_preference_for_qualifying():
    agg = AttendanceAggregator()
    start = datetime(2025, 10, 19, 8, 0, 0)
    end = datetime(2025, 10, 19, 10, 0, 0)
    session = SimpleSession(start, end)

    students = [{
        "student_id": "BIS/789012",
        "student_name": "Fay Martinez",
        "email": "fay.martinez@student.university.ac.ke",
        "program": "Information Systems",
        "stream": "Stream B",
    }]
    attendance = [
        {"student_id": "BIS/789012", "time_recorded": start + timedelta(minutes=1), "within_radius": False, "latitude": "-1.350000", "longitude": "36.900000"},
        {"student_id": "BIS/789012", "time_recorded": start + timedelta(minutes=2), "within_radius": True, "latitude": "-1.286389", "longitude": "36.817223"},
    ]

    rows = agg.classify(session, students, attendance)
    r = rows[0]
    assert r.status == "Present"
    # diagnostics should prefer the qualifying record (within_radius True)
    assert r.latitude == "-1.286389"
