"""Pytest fixtures and common test utilities for reporting application layer."""
import pytest
from datetime import datetime
from reporting.domain.entities.report import Report
from reporting.domain.services.attendance_aggregator import AttendanceAggregator


# ====================
# Fake Repository
# ====================


class FakeReportRepository:
    """Reusable fake repository for all tests."""

    def __init__(self):
        self.created_report = None
        self.updated_export = None
        # Create multiple reports for different test scenarios
        self.reports = {
            2: Report(id=2, session_id=10, generated_by=5),  # not exported
            30: Report(id=30, session_id=10, generated_by=5),  # not exported
            100: Report(id=100, session_id=10, generated_by=5),  # not exported  
            123: Report(id=123, session_id=10, generated_by=5),  # default
        }
        self.session = None  # Can be set to None in tests

    def get_session(self, session_id):
        """Return a mock session with owner_id=5, or None if explicitly set."""
        if self.session is None and hasattr(self, '_session_explicitly_none'):
            return None

        class SimpleSession:
            def __init__(self):
                self.id = session_id
                self.owner_id = 5  # Default owner
                self.start_time = datetime(2025, 10, 19, 8, 0, 0)
                self.end_time = datetime(2025, 10, 19, 10, 0, 0)

        return SimpleSession()

    def get_eligible_students(self, session_id):
        """Return realistic test students with all required fields."""
        return [
            {
                "student_id": "BCS/234344",
                "student_name": "Alice Johnson",
                "email": "alice@student.edu",
                "program": "Computer Science",
                "stream": "Stream A",
            },
            {
                "student_id": "BCS/234345",
                "student_name": "Bob Smith",
                "email": "bob@student.edu",
                "program": "Computer Science",
                "stream": "Stream A",
            },
        ]

    def get_attendance_for_session(self, session_id):
        """Return one attendance record for first student."""
        return [
            {
                "student_id": "BCS/234344",
                "time_recorded": datetime(2025, 10, 19, 8, 5, 0),
                "within_radius": True,
                "latitude": "-1.286389",
                "longitude": "36.817223",
            }
        ]

    def create_report(self, session_id, generated_by, metadata):
        """Create and return a mock report."""
        r = Report(id=123, session_id=session_id, generated_by=generated_by, generated_date="2025-10-24T00:00:00Z")
        self.created_report = r
        return r

    def get_report(self, report_id):
        """Return mock report if id exists in reports dict."""
        return self.reports.get(report_id)

    def get_report_details(self, report_id):
        """Return payload for export."""
        if report_id not in self.reports:
            return None
        return {
            "session": {"id": 10},
            "students": [{"student_id": "BCS/234344", "status": "Present"}],
            "statistics": {"total_students": 2, "present_count": 1},
        }

    def update_export_details(self, report_id, file_path, file_type):
        """Track export updates."""
        self.updated_export = (report_id, file_path, file_type)


# ====================
# Fake Exporter
# ====================


class FakeExporter:
    """Minimal exporter for tests."""

    def export_bytes(self, payload):
        students = payload.get("students", [])
        rows = [f"{s.get('student_id')},{s.get('status')}" for s in students]
        return "\n".join(rows).encode("utf-8")


class FakeExporterFactory:
    """Factory returning FakeExporter."""

    def get_exporter(self, file_type):
        return FakeExporter()


# ====================
# Fake Storage
# ====================


class FakeStorage:
    """In-memory storage for tests."""

    def __init__(self):
        self.saved = {}

    def save_export(self, content_bytes, filename_hint):
        path = f"/tmp/{filename_hint}"
        self.saved[path] = content_bytes
        return path


# ====================
# Pytest Fixtures
# ====================


@pytest.fixture
def fake_repo():
    """Provide a fake report repository."""
    return FakeReportRepository()


@pytest.fixture
def fake_exporter_factory():
    """Provide a fake exporter factory."""
    return FakeExporterFactory()


@pytest.fixture
def fake_storage():
    """Provide fake storage."""
    return FakeStorage()


@pytest.fixture
def attendance_aggregator():
    """Provide real AttendanceAggregator."""
    return AttendanceAggregator()


# ====================
# Test User Fixtures
# ====================


@pytest.fixture
def admin_user():
    """Admin user for authorization tests."""
    return {"id": 1, "role": "admin"}


@pytest.fixture
def lecturer_owner():
    """Lecturer who owns session (id=5 matches FakeRepo owner_id)."""
    return {"id": 5, "role": "lecturer"}


@pytest.fixture
def lecturer_non_owner():
    """Lecturer who doesn't own session."""
    return {"id": 99, "role": "lecturer"}


@pytest.fixture
def student_user():
    """Student user for authorization tests."""
    return {"id": 10, "role": "student"}
