"""Tests for ViewReportUseCase."""
import pytest
from reporting.application.use_cases.view_report import ViewReportUseCase
from reporting.domain.services.report_generator import ReportGenerator
from reporting.domain.exceptions import ReportNotFoundError


def test_view_report_success(fake_repo, attendance_aggregator, lecturer_owner):
    generator = ReportGenerator(attendance_aggregator)
    uc = ViewReportUseCase(fake_repo, generator)
    dto = uc.execute(100, lecturer_owner)

    assert dto.report_id == 100
    assert dto.statistics.present_count >= 1
    assert len(dto.students) >= 1
    assert dto.export_status == "not_exported"


def test_view_report_not_found(fake_repo, attendance_aggregator, admin_user):
    generator = ReportGenerator(attendance_aggregator)
    uc = ViewReportUseCase(fake_repo, generator)

    with pytest.raises(ReportNotFoundError) as exc:
        uc.execute(999, admin_user)
    
    assert "999" in str(exc.value)


def test_view_report_permission_denied(fake_repo, attendance_aggregator, lecturer_non_owner):
    generator = ReportGenerator(attendance_aggregator)
    uc = ViewReportUseCase(fake_repo, generator)

    from reporting.domain.exceptions import UnauthorizedReportAccessError
    with pytest.raises(UnauthorizedReportAccessError) as exc:
        uc.execute(100, lecturer_non_owner)
    
    assert "not allowed" in str(exc.value)


def test_view_report_admin_can_view_any(fake_repo, attendance_aggregator, admin_user):
    generator = ReportGenerator(attendance_aggregator)
    uc = ViewReportUseCase(fake_repo, generator)
    
    dto = uc.execute(100, admin_user)
    
    assert dto.report_id == 100
    assert dto.statistics.present_count >= 1

    # Admin can view any report
    dto = uc.execute(100, admin_user)

    assert dto.report_id == 100
    assert dto.statistics.present_count == 1
