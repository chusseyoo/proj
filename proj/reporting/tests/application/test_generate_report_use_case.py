"""Tests for GenerateReportUseCase."""
from reporting.application.use_cases.generate_report import GenerateReportUseCase
from reporting.domain.services.attendance_aggregator import AttendanceAggregator
from reporting.domain.entities.report import Report


class FakeRepo:
    def __init__(self):
        self.created = None

    def get_session(self, session_id):
        class SimpleSession:
            def __init__(self):
                from datetime import datetime
                self.id = session_id
                self.owner_id = 5
                self.title = "Intro"
                self.start_time = datetime(2025, 10, 19, 8, 0, 0)
                self.end_time = datetime(2025, 10, 19, 10, 0, 0)

        return SimpleSession()

    def get_eligible_students(self, session_id):
        return [{"student_id": "s1", "student_name": "A"}, {"student_id": "s2", "student_name": "B"}]

    def get_attendance_for_session(self, session_id):
        return [
            {"student_id": "s1", "time_recorded": "2025-10-19T08:05:00", "within_radius": True, "latitude": "1", "longitude": "2"}
        ]

    def create_report(self, session_id, generated_by, metadata):
        r = Report(id=123, session_id=session_id, generated_by=generated_by, generated_date="2025-10-24T00:00:00Z")
        self.created = r
        return r


def test_generate_report_happy_path():
    repo = FakeRepo()
    agg = AttendanceAggregator()
    uc = GenerateReportUseCase(repo, agg)
    requested_by = {"id": 5, "role": "lecturer"}

    dto = uc.execute(10, requested_by)

    assert dto.report_id == 123
    assert dto.statistics.present_count == 1
    assert len(dto.students) == 2
    row_map = {r.student_id: r for r in dto.students}
    assert row_map["s1"].status == "Present"
    assert row_map["s2"].status == "Absent"


def test_generate_report_permission_denied():
    """Requester is not the session owner and not an admin -> PermissionError."""
    repo = FakeRepo()
    agg = AttendanceAggregator()
    uc = GenerateReportUseCase(repo, agg)

    # requester is a lecturer but not the owner (owner_id in FakeRepo is 5)
    requested_by = {"id": 99, "role": "lecturer"}

    try:
        uc.execute(10, requested_by)
        raised = False
    except PermissionError as exc:
        raised = True
        assert "not allowed" in str(exc)

    assert raised, "GenerateReportUseCase did not raise PermissionError for unauthorized requester"


def test_generate_report_session_not_found():
    """If the session cannot be found, raise ValueError."""
    class RepoNoSession(FakeRepo):
        def get_session(self, session_id):
            return None

    repo = RepoNoSession()
    agg = AttendanceAggregator()
    uc = GenerateReportUseCase(repo, agg)

    import pytest

    with pytest.raises(ValueError) as exc:
        uc.execute(10, {"id": 5, "role": "lecturer"})

    assert "session 10 not found" in str(exc.value)


def test_generate_report_create_fails():
    """If repository.create_report raises, the exception should propagate."""
    class RepoCreateFails(FakeRepo):
        def create_report(self, session_id, generated_by, metadata):
            raise RuntimeError("db error")

    repo = RepoCreateFails()
    agg = AttendanceAggregator()
    uc = GenerateReportUseCase(repo, agg)

    import pytest

    with pytest.raises(RuntimeError) as exc:
        uc.execute(10, {"id": 5, "role": "lecturer"})

    assert "db error" in str(exc.value)
