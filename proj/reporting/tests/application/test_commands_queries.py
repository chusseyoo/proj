"""Tests for commands and queries dataclasses."""
from reporting.application.commands_queries import (
    GenerateReportCommand,
    ExportReportCommand,
    ViewReportQuery,
    ListReportsQuery,
    DownloadReportQuery,
)


def test_generate_report_command():
    cmd = GenerateReportCommand(session_id=10, requested_by={"id": 5, "role": "lecturer"})
    assert cmd.session_id == 10
    assert cmd.requested_by["id"] == 5


def test_export_report_command():
    cmd = ExportReportCommand(report_id=100, file_type="csv", requested_by={"id": 5, "role": "admin"})
    assert cmd.report_id == 100
    assert cmd.file_type == "csv"


def test_view_report_query():
    query = ViewReportQuery(report_id=50, requested_by={"id": 10, "role": "lecturer"})
    assert query.report_id == 50


def test_list_reports_query():
    query = ListReportsQuery(
        requested_by={"id": 1, "role": "admin"},
        session_id=20,
        page=2,
        page_size=50,
    )
    assert query.session_id == 20
    assert query.page == 2
    assert query.page_size == 50


def test_list_reports_query_defaults():
    query = ListReportsQuery(requested_by={"id": 1, "role": "admin"})
    assert query.page == 1
    assert query.page_size == 20
    assert query.session_id is None


def test_download_report_query():
    query = DownloadReportQuery(report_id=75, requested_by={"id": 5, "role": "lecturer"})
    assert query.report_id == 75
