"""Unit tests for the reporting `Report` domain entity."""
from reporting.domain.entities.report import Report
from reporting.domain.exceptions import ReportingError


def test_report_validate_and_mark_exported():
    r = Report(id=None, session_id=10, generated_by=5)
    # validate should not raise for valid data
    r.validate()

    assert not r.is_exported()
    r.mark_exported(file_path="/tmp/report.csv", file_type="csv")
    assert r.is_exported()
    assert r.file_path == "/tmp/report.csv"
    assert r.file_type == "csv"
    assert r.generated_date is not None


def test_to_from_dict_roundtrip():
    r = Report(id=1, session_id=20, generated_by=7, generated_date="2025-01-01T00:00:00Z", file_path="/a/b", file_type="csv")
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
