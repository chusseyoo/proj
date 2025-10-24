"""Use-case: generate a report for a session.

This module contains a minimal scaffold for the GenerateReport use-case.
It should be implemented to orchestrate fetching session metadata, eligible
students, attendance records, aggregate them using AttendanceAggregator and
return a ReportDTO.
"""
from typing import Any

from reporting.application.dto.report_dto import ReportDTO


class GenerateReportUseCase:
    """Orchestrates report generation.

    Constructor should accept repositories/services needed to build the report.
    """

    def __init__(self, report_repository: Any, attendance_aggregator: Any):
        self.report_repository = report_repository
        self.attendance_aggregator = attendance_aggregator

    def execute(self, session_id: int, requested_by: Any) -> ReportDTO:
        """Generate and persist a view-only Report record and return a ReportDTO.

        - Validate permissions (lecturer owns session or admin)
        - Fetch session and eligible students
        - Fetch attendance records for session
        - Use attendance_aggregator.classify(...) to build student rows
        - Compute statistics and assemble ReportDTO
        - Persist Report metadata via report_repository.create_report(...)

        Returns ReportDTO
        """
        # TODO: implement the use-case orchestration
        raise NotImplementedError("GenerateReportUseCase.execute not implemented")
