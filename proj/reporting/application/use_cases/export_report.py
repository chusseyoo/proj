"""Application use-case: export a previously generated report file.

Orchestration:
- validate report exists and is not already exported
- fetch report payload (session, students, statistics)
- produce bytes using an exporter from exporter_factory
- persist bytes via storage_adapter.save_export
- update repository with export details
"""
from typing import Any

from reporting.application.dto.report_dto import ExportResultDTO
from reporting.domain.ports import ReportRepositoryPort
from reporting.domain.services.report_access_policy import ReportAccessPolicy
from reporting.domain.exceptions import ReportNotFoundError, ReportAlreadyExportedError


class ExportReportUseCase:
	def __init__(self, report_repository: ReportRepositoryPort, exporter_factory: Any, storage_adapter: Any, access_policy: ReportAccessPolicy | None = None):
		self.repo = report_repository
		self.exporter_factory = exporter_factory
		self.storage = storage_adapter
		self.access_policy = access_policy or ReportAccessPolicy()

	def execute(self, report_id: int, file_type: str, requested_by: Any) -> ExportResultDTO:
		# permission check
		self.access_policy.ensure_can_export(requested_by)

		# load report
		report = self.repo.get_report(report_id)
		if not report:
			raise ReportNotFoundError(f"report {report_id} not found")

		if getattr(report, "file_path", None):
			raise ReportAlreadyExportedError("report already exported")

		payload = self.repo.get_report_details(report_id)
		if not payload:
			raise ValueError("report payload not available for export")

		exporter = self.exporter_factory.get_exporter(file_type)
		content_bytes = exporter.export_bytes(payload)

		# filename hint
		session = payload.get("session") or {}
		session_id = session.get("id") if isinstance(session, dict) else getattr(session, "id", None)
		filename_hint = f"session_{session_id or report_id}_report.{file_type}"

		final_path = self.storage.save_export(content_bytes, filename_hint)

		self.repo.update_export_details(report_id, final_path, file_type)

		generated_date = getattr(report, "generated_date", None)
		download_url = f"/api/v1/reports/{report_id}/download/"

		return ExportResultDTO(
			report_id=report_id,
			file_path=final_path,
			file_type=file_type,
			download_url=download_url,
			generated_date=generated_date,
		)

