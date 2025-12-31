"""Unit tests for the reporting `Report` domain entity."""
from reporting.domain.entities.report import Report
from reporting.domain.exceptions import ReportingError


def test_report_validate_and_mark_exported():
    r = Report(id=None, session_id=10, generated_by=5)
    # validate should not raise for valid data
    r.validate()

    assert not r.is_exported()
    r.mark_exported(file_path="/media/reports/2025/10/session_10_20251019143022.csv", file_type="csv")
    assert r.is_exported()
    assert r.file_path == "/media/reports/2025/10/session_10_20251019143022.csv"
    assert r.file_type == "csv"
    assert r.generated_date is not None


def test_to_from_dict_roundtrip():
    r = Report(id=1, session_id=20, generated_by=7, generated_date="2025-01-01T00:00:00Z", file_path="/media/reports/2025/01/session_20_20250101120000.csv", file_type="csv")
    d = r.to_dict()
    r2 = Report.from_dict(d)
    assert r2.session_id == 20
    assert r2.generated_by == 7
    assert r2.file_type == "csv"


def test_invalid_report_validation():
    r = Report(id=None, session_id=0, generated_by=0)
    try:
        r.validate()
        assert False, "validate should have raised"
    except ReportingError:
        pass


def test_report_mark_exported_excel():
    r = Report(id=2, session_id=15, generated_by=3)
    r.mark_exported(file_path="/media/reports/2025/10/session_15_20251019150000.xlsx", file_type="excel")
    assert r.is_exported()
    assert r.file_path == "/media/reports/2025/10/session_15_20251019150000.xlsx"
    assert r.file_type == "excel"
    assert r.generated_date is not None
