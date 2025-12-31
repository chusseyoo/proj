"""Tests for DownloadReportUseCase."""
from reporting.application.use_cases.download_report import DownloadReportUseCase
from reporting.domain.entities.report import Report
from reporting.domain.exceptions import ReportNotFoundError


class FakeRepoForDownload:
    def __init__(self):
        self.report_with_file = Report(
            id=50,
            session_id=10,
            generated_by=5,
            file_path="/media/reports/2025/10/session_10_20251019143022.csv",
            file_type="csv",
        )
        self.report_no_file = Report(id=51, session_id=11, generated_by=5, file_path=None, file_type=None)

    def get_report(self, report_id):
        if report_id == 50:
            return self.report_with_file
        elif report_id == 51:
            return self.report_no_file
        return None


def test_download_report_success():
    repo = FakeRepoForDownload()
    uc = DownloadReportUseCase(repo)

    requested_by = {"id": 5, "role": "lecturer"}
    result = uc.execute(50, requested_by)

    assert result.file_path == "/media/reports/2025/10/session_10_20251019143022.csv"
    assert result.file_type == "csv"
    assert result.filename == "session_10_20251019143022.csv"


def test_download_report_not_found():
    repo = FakeRepoForDownload()
    uc = DownloadReportUseCase(repo)

    requested_by = {"id": 5, "role": "admin"}

    try:
        uc.execute(999, requested_by)
        assert False, "Should have raised ReportNotFoundError"
    except ReportNotFoundError as exc:
        assert "report 999 not found" in str(exc)


def test_download_report_not_exported():
    repo = FakeRepoForDownload()
    uc = DownloadReportUseCase(repo)

    requested_by = {"id": 5, "role": "lecturer"}

    try:
        uc.execute(51, requested_by)
        assert False, "Should have raised ValueError for not exported report"
    except ValueError as exc:
        assert "not been exported" in str(exc)


def test_download_report_permission_student():
    repo = FakeRepoForDownload()
    uc = DownloadReportUseCase(repo)

    requested_by = {"id": 10, "role": "student"}

    try:
        uc.execute(50, requested_by)
        assert False, "Students should not be able to download reports"
    except Exception as exc:
        assert "not allowed" in str(exc).lower()
