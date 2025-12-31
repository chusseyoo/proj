"""Handler behavior tests for reporting API layer."""
from dataclasses import dataclass, field

from reporting.interfaces.api.handlers.generate_report_handler import GenerateReportHandler
from reporting.interfaces.api.handlers.export_report_handler import ExportReportHandler
from reporting.interfaces.api.handlers.download_report_handler import DownloadReportHandler
from reporting.application.dto.report_dto import (
    ReportDTO,
    StatisticsDTO,
    StudentRowDTO,
    ExportResultDTO,
)
from reporting.application.use_cases.download_report import DownloadFileResult


class _User:
    def __init__(self, user_id: int, role: str):
        self.id = user_id
        self.role = role


def test_generate_report_handler_serializes_response():
    # Minimal fake session with required attributes
    @dataclass
    class _Course:
        name: str = "Course"
        code: str = "CRS101"

    @dataclass
    class _Program:
        name: str = "Program"
        code: str = "PRG"

    @dataclass
    class _Session:
        session_id: int = 10
        course: _Course = field(default_factory=_Course)
        program: _Program = field(default_factory=_Program)
        stream: None = None
        time_created: str = "2025-01-01T00:00:00Z"
        time_ended: str = "2025-01-01T01:00:00Z"
        lecturer: None = None

    stats = StatisticsDTO(
        total_students=2,
        present_count=1,
        present_percentage=50.0,
        absent_count=1,
        absent_percentage=50.0,
    )
    students = [
        StudentRowDTO(
            student_id="S1",
            student_name="Alice",
            email="a@example.com",
            program="CS",
            stream="A",
            status="Present",
            time_recorded="2025-01-01T00:00:00Z",
            within_radius=True,
            latitude="0.0",
            longitude="0.0",
        )
    ]

    report_dto = ReportDTO(
        report_id=5,
        session=_Session(),
        statistics=stats,
        students=students,
        generated_date="2025-01-01T00:00:00Z",
        generated_by="lecturer-1",
        export_status="not_exported",
    )

    class FakeUseCase:
        def execute(self, session_id, requested_by):
            return report_dto

    handler = GenerateReportHandler(generate_report_use_case=FakeUseCase())
    result = handler.handle(session_id=10, requested_by=_User(1, "lecturer"))

    assert result["report_id"] == 5
    assert result["statistics"]["present_count"] == 1
    assert result["students"][0]["student_id"] == "S1"
    assert result["export_status"] == "not_exported"


def test_export_report_handler_formats_result():
    export_result = ExportResultDTO(
        report_id=7,
        file_path="/tmp/file.csv",
        file_type="csv",
        download_url="/api/v1/reports/7/download/",
        generated_date=None,
    )

    class FakeUseCase:
        def execute(self, report_id, file_type, requested_by):
            return export_result

    handler = ExportReportHandler(export_use_case=FakeUseCase())
    out = handler.handle(report_id=7, file_type="csv", requested_by=_User(2, "admin"))

    assert out["report_id"] == 7
    assert out["file_type"] == "csv"
    assert out["download_url"].endswith("/download/")


def test_download_report_handler_returns_dto():
    download_result = DownloadFileResult(
        file_path="/tmp/report.csv",
        file_type="csv",
        filename="report.csv",
    )

    class FakeUseCase:
        def execute(self, report_id, requested_by):
            return download_result

    handler = DownloadReportHandler(download_use_case=FakeUseCase())
    out = handler.handle(report_id=9, requested_by=_User(3, "admin"))

    assert isinstance(out, DownloadFileResult)
    assert out.file_type == "csv"
