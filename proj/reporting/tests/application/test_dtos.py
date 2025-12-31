"""Tests for DTOs."""
from reporting.application.dto.report_dto import (
    StudentRowDTO,
    StatisticsDTO,
    ReportDTO,
    ExportResultDTO,
    DownloadFileDTO,
)


def test_student_row_dto():
    row = StudentRowDTO(
        student_id="BCS/234344",
        student_name="Alice Johnson",
        email="alice@test.com",
        program="Computer Science",
        stream="Stream A",
        status="Present",
        time_recorded="2025-10-19T08:05:00Z",
        within_radius=True,
        latitude="-1.286389",
        longitude="36.817223",
    )
    assert row.student_id == "BCS/234344"
    assert row.status == "Present"
    assert row.within_radius is True


def test_statistics_dto():
    stats = StatisticsDTO(
        total_students=50,
        present_count=35,
        present_percentage=70.0,
        absent_count=15,
        absent_percentage=30.0,
        within_radius_count=40,
        outside_radius_count=3,
    )
    assert stats.total_students == 50
    assert stats.present_count == 35
    assert stats.within_radius_count == 40


def test_report_dto():
    stats = StatisticsDTO(
        total_students=10,
        present_count=8,
        present_percentage=80.0,
        absent_count=2,
        absent_percentage=20.0,
    )
    row = StudentRowDTO(
        student_id="BCS/234344",
        student_name="Alice",
        email="alice@test.com",
        program="CS",
        stream="A",
        status="Present",
        time_recorded="2025-10-19T08:05:00Z",
        within_radius=True,
        latitude="-1.286389",
        longitude="36.817223",
    )

    report = ReportDTO(
        report_id=100,
        session={"session_id": 10},
        statistics=stats,
        students=[row],
        generated_date="2025-10-19T14:00:00Z",
        generated_by="5",
        export_status="not_exported",
    )

    assert report.report_id == 100
    assert report.export_status == "not_exported"
    assert len(report.students) == 1


def test_export_result_dto():
    result = ExportResultDTO(
        report_id=100,
        file_path="/media/reports/2025/10/session_10_20251019143022.csv",
        file_type="csv",
        download_url="/api/v1/reports/100/download/",
        generated_date="2025-10-19T14:00:00Z",
    )
    assert result.report_id == 100
    assert result.file_type == "csv"
    assert "download" in result.download_url


def test_download_file_dto():
    dto = DownloadFileDTO(
        file_path="/media/reports/test.csv",
        file_type="csv",
        filename="test.csv",
        content_type="text/csv",
    )
    assert dto.file_type == "csv"
    assert dto.content_type == "text/csv"


def test_download_file_dto_from_export_result_csv():
    dto = DownloadFileDTO.from_export_result(
        file_path="/media/reports/test.csv",
        file_type="csv",
        filename="test.csv",
    )
    assert dto.content_type == "text/csv"


def test_download_file_dto_from_export_result_excel():
    dto = DownloadFileDTO.from_export_result(
        file_path="/media/reports/test.xlsx",
        file_type="excel",
        filename="test.xlsx",
    )
    assert dto.content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
