"""Tests for ListReportsUseCase."""
import pytest
from reporting.application.use_cases.list_reports import ListReportsUseCase
from reporting.domain.exceptions import UnauthorizedReportAccessError


def test_list_reports_admin_only(fake_repo, admin_user):
    uc = ListReportsUseCase(fake_repo)
    result = uc.execute(admin_user)

    # Currently returns empty as repo method not implemented
    assert result.reports == []
    assert result.pagination.current_page == 1


def test_list_reports_lecturer_forbidden(fake_repo, lecturer_owner):
    uc = ListReportsUseCase(fake_repo)

    with pytest.raises(UnauthorizedReportAccessError) as exc:
        uc.execute(lecturer_owner)
    
    assert "administrators" in str(exc.value)


def test_list_reports_student_forbidden(fake_repo, student_user):
    uc = ListReportsUseCase(fake_repo)

    with pytest.raises(UnauthorizedReportAccessError) as exc:
        uc.execute(student_user)
    
    assert "administrators" in str(exc.value)


def test_list_reports_with_filters(fake_repo, admin_user):
    uc = ListReportsUseCase(fake_repo)
    result = uc.execute(admin_user, session_id=10, page=2, page_size=50)

    assert result.pagination.current_page == 2
    assert result.pagination.page_size == 50
