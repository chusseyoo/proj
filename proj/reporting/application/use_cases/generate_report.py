"""Application use-case: generate a report for a session.

This use-case orchestrates fetching session/students/attendance from a
repository port, classifying attendance via the domain aggregator, computing
statistics, persisting a report record and returning a ReportDTO.
"""
from dataclasses import asdict
from typing import Any

from reporting.application.dto.report_dto import ReportDTO, StatisticsDTO
from reporting.domain.ports import ReportRepositoryPort
from reporting.domain.services.attendance_aggregator import AttendanceAggregator


class GenerateReportUseCase:
	def __init__(self, report_repository: ReportRepositoryPort, attendance_aggregator: AttendanceAggregator):
		self.report_repository = report_repository
		self.attendance_aggregator = attendance_aggregator

	def execute(self, session_id: int, requested_by: Any) -> ReportDTO:
		# fetch session
		session = self.report_repository.get_session(session_id)
		if not session:
			raise ValueError(f"session {session_id} not found")

		# extract requester info
		if isinstance(requested_by, dict):
			user_id = requested_by.get("id")
			role = requested_by.get("role")
		else:
			user_id = getattr(requested_by, "id", None)
			role = getattr(requested_by, "role", None)

		# permission check: admin or lecturer and owner
		if role != "admin":
			owner_id = session.get("owner_id") if isinstance(session, dict) else getattr(session, "owner_id", None)
			if role != "lecturer" or owner_id != user_id:
				raise PermissionError("not allowed to generate this report")

		# fetch data
		eligible_students = list(self.report_repository.get_eligible_students(session_id))
		attendance_records = list(self.report_repository.get_attendance_for_session(session_id))

		# classify
		rows = self.attendance_aggregator.classify(session, eligible_students, attendance_records)

		# compute statistics
		from reporting.domain.services.statistics_calculator import compute_statistics

		rows_mapped = [asdict(r) if hasattr(r, "__dataclass_fields__") else r for r in rows]
		stats = compute_statistics(rows_mapped)
		stats_dto = StatisticsDTO(**stats)

		# persist report metadata
		created = self.report_repository.create_report(session_id, int(user_id), metadata={
			"session": session,
			"statistics": stats,
		})

		report_id = getattr(created, "id", created)
		generated_date = getattr(created, "generated_date", None)
		export_status = "exported" if getattr(created, "file_path", None) else "not_exported"

		return ReportDTO(
			report_id=report_id,
			session=session,
			statistics=stats_dto,
			students=rows,
			generated_date=generated_date,
			generated_by=str(user_id),
			export_status=export_status,
		)

