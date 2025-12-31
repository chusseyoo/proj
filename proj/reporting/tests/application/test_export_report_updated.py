"""Tests for ExportReportUseCase with updated exception handling."""
import pytest
from reporting.application.use_cases.export_report import ExportReportUseCase
from reporting.domain.entities.report import Report
from reporting.domain.exceptions import ReportNotFoundError, ReportAlreadyExportedError


def test_export_report_success(fake_repo, fake_exporter_factory, fake_storage, lecturer_owner):
    uc = ExportReportUseCase(fake_repo, fake_exporter_factory, fake_storage)
    result = uc.execute(30, "csv", lecturer_owner)

    assert result.report_id == 30
    assert result.file_type == "csv"
    assert "/tmp/" in result.file_path or "/media/reports/" in result.file_path
    assert result.download_url == "/api/v1/reports/30/download/"
    assert fake_repo.updated_export[0] == 30


def test_export_report_not_found(fake_repo, fake_exporter_factory, fake_storage, admin_user):
    uc = ExportReportUseCase(fake_repo, fake_exporter_factory, fake_storage)

    with pytest.raises(ReportNotFoundError) as exc:
        uc.execute(999, "csv", admin_user)
    
    assert "999" in str(exc.value)


def test_export_report_already_exported(fake_repo, fake_exporter_factory, fake_storage, lecturer_owner):
    # Mark report as already exported
    fake_repo.reports[30].file_path = "/media/reports/existing.csv"
    fake_repo.reports[30].file_type = "csv"
    
    uc = ExportReportUseCase(fake_repo, fake_exporter_factory, fake_storage)

    with pytest.raises(ReportAlreadyExportedError) as exc:
        uc.execute(30, "csv", lecturer_owner)
    
    assert "already exported" in str(exc.value)


def test_export_report_student_forbidden(fake_repo, fake_exporter_factory, fake_storage, student_user):
    uc = ExportReportUseCase(fake_repo, fake_exporter_factory, fake_storage)

    with pytest.raises(Exception) as exc:
        uc.execute(2, "csv", student_user)
    
    assert "not allowed" in str(exc.value).lower()


def test_export_report_excel_format(fake_repo, fake_exporter_factory, fake_storage, admin_user):
    uc = ExportReportUseCase(fake_repo, fake_exporter_factory, fake_storage)

    result = uc.execute(2, "excel", admin_user)

    assert result.file_type == "excel"
    assert result.report_id == 2
