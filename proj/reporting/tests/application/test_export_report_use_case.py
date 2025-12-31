"""Tests for ExportReportUseCase."""
import pytest
from reporting.application.use_cases.export_report import ExportReportUseCase
from reporting.domain.entities.report import Report
from reporting.domain.exceptions.core import ReportNotFoundError, ReportAlreadyExportedError


def test_export_report_happy_path(fake_repo, fake_exporter_factory, fake_storage, admin_user):
    uc = ExportReportUseCase(fake_repo, fake_exporter_factory, fake_storage)

    result = uc.execute(2, file_type="csv", requested_by=admin_user)
    assert result.file_type == "csv"
    assert "/media/reports/" in result.file_path or "/tmp/" in result.file_path
    assert fake_repo.updated_export is not None


def test_export_report_missing_report(fake_repo, fake_exporter_factory, fake_storage, admin_user):
    """If the report does not exist, raise ReportNotFoundError."""
    uc = ExportReportUseCase(fake_repo, fake_exporter_factory, fake_storage)

    with pytest.raises(ReportNotFoundError) as exc:
        uc.execute(999, file_type="csv", requested_by=admin_user)

    assert "999" in str(exc.value)


def test_export_report_already_exported(fake_repo, fake_exporter_factory, fake_storage, admin_user):
    """If the report already has a file_path, exporting should be blocked."""
    # Mark report as already exported
    fake_repo.reports[30].file_path = "/tmp/already"
    fake_repo.reports[30].file_type = "csv"

    uc = ExportReportUseCase(fake_repo, fake_exporter_factory, fake_storage)

    with pytest.raises(ReportAlreadyExportedError) as exc:
        uc.execute(30, file_type="csv", requested_by=admin_user)

    assert "already exported" in str(exc.value)


def test_export_report_storage_failure(fake_repo, fake_exporter_factory, admin_user):
    """If storage.save_export raises, ensure exception propagates and repo.update_export_details is not called."""
    from reporting.tests.conftest import FakeStorage
    
    class BrokenStorage(FakeStorage):
        def save_export(self, content_bytes, filename_hint):
            raise IOError("disk full")

    storage = BrokenStorage()
    uc = ExportReportUseCase(fake_repo, fake_exporter_factory, storage)

    with pytest.raises(IOError) as exc:
        uc.execute(2, file_type="csv", requested_by=admin_user)

    assert "disk full" in str(exc.value)
    assert fake_repo.updated_export is None
