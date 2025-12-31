"""Tests for GenerateReportUseCase."""
import pytest
from reporting.application.use_cases.generate_report import GenerateReportUseCase
from reporting.domain.entities.report import Report
from reporting.domain.exceptions.core import UnauthorizedReportAccessError, SessionNotFoundError


def test_generate_report_happy_path(fake_repo, attendance_aggregator, lecturer_owner):
    uc = GenerateReportUseCase(fake_repo, attendance_aggregator)

    dto = uc.execute(10, lecturer_owner)

    assert dto.report_id == 123
    assert dto.statistics.present_count >= 1
    assert len(dto.students) >= 1


def test_generate_report_permission_denied(fake_repo, attendance_aggregator, lecturer_non_owner):
    """Requester is not the session owner and not an admin -> UnauthorizedReportAccessError."""
    uc = GenerateReportUseCase(fake_repo, attendance_aggregator)

    # requester is a lecturer but not the owner (owner_id in fake_repo is 5)
    with pytest.raises(UnauthorizedReportAccessError) as exc:
        uc.execute(10, lecturer_non_owner)
    
    assert "not allowed" in str(exc.value)


def test_generate_report_session_not_found(fake_repo, attendance_aggregator, lecturer_owner):
    """If the session cannot be found, raise SessionNotFoundError."""
    fake_repo._session_explicitly_none = True
    fake_repo.session = None
    uc = GenerateReportUseCase(fake_repo, attendance_aggregator)

    with pytest.raises(SessionNotFoundError) as exc:
        uc.execute(10, lecturer_owner)

    assert "10" in str(exc.value)
    # Override get_session to return None
    fake_repo.session_data = None

    uc = GenerateReportUseCase(fake_repo, attendance_aggregator)

    with pytest.raises(SessionNotFoundError) as exc:
        uc.execute(10, lecturer_owner)

    assert "10" in str(exc.value)


def test_generate_report_create_fails(fake_repo, attendance_aggregator, lecturer_owner):
    """If repository.create_report raises, the exception should propagate."""
    # Override create_report to raise error
    original_create = fake_repo.create_report
    fake_repo.create_report = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("db error"))

    uc = GenerateReportUseCase(fake_repo, attendance_aggregator)

    with pytest.raises(RuntimeError) as exc:
        uc.execute(10, lecturer_owner)

    assert "db error" in str(exc.value)
