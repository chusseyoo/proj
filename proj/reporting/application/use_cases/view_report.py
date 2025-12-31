"""Application use-case: view an existing report.

This use-case retrieves report data for display without creating a new report.
Data is re-queried from current state (not a snapshot).
"""
from typing import Any

from reporting.application.dto.report_dto import ReportDTO, StatisticsDTO, StudentRowDTO
from reporting.domain.ports import ReportRepositoryPort
from reporting.domain.services.report_generator import ReportGenerator
from reporting.domain.services.report_access_policy import ReportAccessPolicy
from reporting.domain.exceptions import ReportNotFoundError


class ViewReportUseCase:
    def __init__(
        self,
        report_repository: ReportRepositoryPort,
        report_generator: ReportGenerator,
        access_policy: ReportAccessPolicy | None = None,
    ):
        self.repo = report_repository
        self.report_generator = report_generator
        self.access_policy = access_policy or ReportAccessPolicy()

    def execute(self, report_id: int, requested_by: Any) -> ReportDTO:
        # load report metadata
        report = self.repo.get_report(report_id)
        if not report:
            raise ReportNotFoundError(f"report {report_id} not found")

        session_id = getattr(report, "session_id", None)
        if not session_id:
            raise ValueError("report has no session_id")

        # fetch session for permission check
        session = self.repo.get_session(session_id)
        if not session:
            raise ValueError(f"session {session_id} not found")

        # permission check
        self.access_policy.ensure_can_generate(session, requested_by)

        # re-query data (current state)
        eligible_students = list(self.repo.get_eligible_students(session_id))
        attendance_records = list(self.repo.get_attendance_for_session(session_id))

        # regenerate classification and stats
        result = self.report_generator.generate(session, eligible_students, attendance_records)
        stats_dto = StatisticsDTO(**result.statistics.to_dict())
        rows_dto = [StudentRowDTO(**row.to_dict()) for row in result.students]

        # extract requester info
        if isinstance(requested_by, dict):
            user_id = requested_by.get("id")
        else:
            user_id = getattr(requested_by, "id", None)

        report_id = getattr(report, "id", report_id)
        generated_date = getattr(report, "generated_date", None)
        generated_by = getattr(report, "generated_by", user_id)
        export_status = "exported" if getattr(report, "file_path", None) else "not_exported"

        return ReportDTO(
            report_id=report_id,
            session=session,
            statistics=stats_dto,
            students=rows_dto,
            generated_date=generated_date,
            generated_by=str(generated_by),
            export_status=export_status,
        )
