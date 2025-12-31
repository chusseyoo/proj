"""HTTP handler glue for generating a report."""
from dataclasses import asdict
from typing import Any, Optional

from reporting.application.dto.report_dto import ReportDTO
from reporting.application.use_cases.generate_report import GenerateReportUseCase
from reporting.domain.services.attendance_aggregator import AttendanceAggregator
from reporting.domain.services.report_generator import ReportGenerator
from reporting.domain.services.report_access_policy import ReportAccessPolicy
from reporting.infrastructure.di import get_report_repository


def _build_use_case() -> GenerateReportUseCase:
    repo = get_report_repository()
    aggregator = AttendanceAggregator()
    generator = ReportGenerator(aggregator)
    access = ReportAccessPolicy()
    return GenerateReportUseCase(repo, aggregator, generator, access)


def _session_to_dict(session: Any) -> dict[str, Any]:
    """Map session model/object to response fields using best-effort attributes."""
    return {
        "session_id": getattr(session, "session_id", getattr(session, "id", None)),
        "course_name": getattr(getattr(session, "course", None), "name", None),
        "course_code": getattr(getattr(session, "course", None), "code", None),
        "program_name": getattr(getattr(session, "program", None), "name", None),
        "program_code": getattr(getattr(session, "program", None), "code", None),
        "stream_name": getattr(getattr(session, "stream", None), "name", None),
        "time_created": getattr(session, "time_created", None),
        "time_ended": getattr(session, "time_ended", None),
        "lecturer_name": getattr(getattr(getattr(session, "lecturer", None), "user", None), "get_full_name", lambda: None)(),
    }


class GenerateReportHandler:
    """Thin handler that wraps the GenerateReport use-case."""

    def __init__(self, generate_report_use_case: Optional[GenerateReportUseCase] = None):
        self.use_case = generate_report_use_case or _build_use_case()

    def handle(self, session_id: int, requested_by: Any) -> dict[str, Any]:
        """Execute the use-case and return formatted response dict."""
        # Normalize requester
        requester = {
            "id": getattr(requested_by, "id", None),
            "role": getattr(requested_by, "role", None),
        }

        report_dto: ReportDTO = self.use_case.execute(session_id, requester)

        # Serialize nested structures
        statistics = asdict(report_dto.statistics)
        students = [asdict(s) for s in report_dto.students]
        session_info = _session_to_dict(report_dto.session)

        return {
            "report_id": report_dto.report_id,
            "session": session_info,
            "statistics": statistics,
            "students": students,
            "generated_date": report_dto.generated_date,
            "generated_by": report_dto.generated_by,
            "export_status": report_dto.export_status,
        }
