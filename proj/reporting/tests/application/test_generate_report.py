"""Small integration-style tests for the generate-report use-case.

These exercises are lightweight and use a fake repository to drive
the use-case behaviour. They intentionally do not touch other apps and
keep the repository behaviour in-process.
"""
import pytest
from reporting.application.use_cases.generate_report import GenerateReportUseCase
from reporting.domain.exceptions.core import UnauthorizedReportAccessError


def test_generate_report_allows_admin(fake_repo, attendance_aggregator, admin_user):
    uc = GenerateReportUseCase(fake_repo, attendance_aggregator)

    # admin can generate any session
    dto = uc.execute(10, {"id": 9, "role": "admin"})

    assert dto.report_id == 123
    assert dto.statistics.present_count == 1
    assert len(dto.students) >= 1


def test_generate_report_denies_non_owner_lecturer(fake_repo, attendance_aggregator, lecturer_non_owner):
    uc = GenerateReportUseCase(fake_repo, attendance_aggregator)

    # lecturer who is not owner should be denied
    with pytest.raises(UnauthorizedReportAccessError):
        uc.execute(10, lecturer_non_owner)

