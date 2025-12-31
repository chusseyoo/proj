"""Application use-case: generate a report for a session.

This use-case orchestrates fetching session/students/attendance from a
repository port, classifying attendance via the domain aggregator, computing
statistics, persisting a report record and returning a ReportDTO.
"""
from typing import Any

from reporting.application.dto.report_dto import ReportDTO, StatisticsDTO, StudentRowDTO
from reporting.domain.ports import ReportRepositoryPort
from reporting.domain.services.attendance_aggregator import AttendanceAggregator
from reporting.domain.services.report_generator import ReportGenerator
from reporting.domain.services.report_access_policy import ReportAccessPolicy
from reporting.domain.exceptions import SessionNotFoundError


class GenerateReportUseCase:
	def __init__(self, report_repository: ReportRepositoryPort, attendance_aggregator: AttendanceAggregator, report_generator: ReportGenerator | None = None, access_policy: ReportAccessPolicy | None = None):
		self.report_repository = report_repository
		self.attendance_aggregator = attendance_aggregator
		self.report_generator = report_generator or ReportGenerator(attendance_aggregator)
		self.access_policy = access_policy or ReportAccessPolicy()

	def execute(self, session_id: int, requested_by: Any) -> ReportDTO:
		# fetch session
		session = self.report_repository.get_session(session_id)
		if not session:
			raise SessionNotFoundError(f"session {session_id} not found")

		# extract requester info
		if isinstance(requested_by, dict):
			user_id = requested_by.get("id")
			role = requested_by.get("role")
		else:
			user_id = getattr(requested_by, "id", None)
			role = getattr(requested_by, "role", None)

		# permission check via domain policy
		self.access_policy.ensure_can_generate(session, requested_by)

		# fetch data
		eligible_students = list(self.report_repository.get_eligible_students(session_id))
		attendance_records = list(self.report_repository.get_attendance_for_session(session_id))

		# generate report data at domain layer (classification + stats)
		result = self.report_generator.generate(session, eligible_students, attendance_records)
		stats_dto = StatisticsDTO(**result.statistics.to_dict())
		rows_dto = [StudentRowDTO(**row.to_dict()) for row in result.students]

		# persist report metadata
		created = self.report_repository.create_report(session_id, int(user_id), metadata=result.to_metadata())

		report_id = getattr(created, "id", created)
		generated_date = getattr(created, "generated_date", None)
		export_status = "exported" if getattr(created, "file_path", None) else "not_exported"

		return ReportDTO(
			report_id=report_id,
			session=session,
			statistics=stats_dto,
			students=rows_dto,
			generated_date=generated_date,
			generated_by=str(user_id),
			export_status=export_status,
		)

