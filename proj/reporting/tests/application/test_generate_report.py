"""Small integration-style tests for the generate-report use-case.

These exercises are lightweight and use a fake repository to drive
the use-case behaviour. They intentionally do not touch other apps and
keep the repository behaviour in-process.
"""
from reporting.application.use_cases.generate_report import GenerateReportUseCase
from reporting.domain.services.attendance_aggregator import AttendanceAggregator
from reporting.domain.entities.report import Report


class RepoDictSession:
    def get_session(self, session_id):
        # return a simple object with attributes (attendance_aggregator expects attrs)
        class SimpleSession:
            def __init__(self):
                from datetime import datetime
                self.id = session_id
                self.owner_id = 1
                self.title = "S1"
                self.start_time = datetime(2025, 10, 19, 8, 0, 0)
                self.end_time = datetime(2025, 10, 19, 10, 0, 0)

        return SimpleSession()

    def get_eligible_students(self, session_id):
        return [{"student_id": "s1", "student_name": "Alice"}]

    def get_attendance_for_session(self, session_id):
        return [{"student_id": "s1", "time_recorded": "2025-10-19T08:05:00", "within_radius": True}]

    def create_report(self, session_id, generated_by, metadata):
        return Report(id=900, session_id=session_id, generated_by=generated_by)


def test_generate_report_allows_admin():
    repo = RepoDictSession()
    agg = AttendanceAggregator()
    uc = GenerateReportUseCase(repo, agg)

    # admin can generate any session
    dto = uc.execute(10, {"id": 9, "role": "admin"})

    assert dto.report_id == 900
    assert dto.statistics.present_count == 1
    assert len(dto.students) == 1


def test_generate_report_denies_non_owner_lecturer():
    repo = RepoDictSession()
    agg = AttendanceAggregator()
    uc = GenerateReportUseCase(repo, agg)

    # lecturer who is not owner should be denied
    import pytest

    with pytest.raises(PermissionError):
        uc.execute(10, {"id": 99, "role": "lecturer"})

