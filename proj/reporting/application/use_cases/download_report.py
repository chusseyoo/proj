"""Application use-case: download an exported report file.

This use-case retrieves the file path and metadata for downloading an exported report.
"""
from typing import Any
from dataclasses import dataclass

from reporting.domain.ports import ReportRepositoryPort
from reporting.domain.services.report_access_policy import ReportAccessPolicy
from reporting.domain.exceptions import ReportNotFoundError


@dataclass
class DownloadFileResult:
    file_path: str
    file_type: str
    filename: str


class DownloadReportUseCase:
    def __init__(self, report_repository: ReportRepositoryPort, access_policy: ReportAccessPolicy | None = None):
        self.repo = report_repository
        self.access_policy = access_policy or ReportAccessPolicy()

    def execute(self, report_id: int, requested_by: Any) -> DownloadFileResult:
        # permission check
        self.access_policy.ensure_can_export(requested_by)

        # load report
        report = self.repo.get_report(report_id)
        if not report:
            raise ReportNotFoundError(f"report {report_id} not found")

        file_path = getattr(report, "file_path", None)
        if not file_path:
            raise ValueError("report has not been exported")

        file_type = getattr(report, "file_type", None)
        session_id = getattr(report, "session_id", report_id)

        # extract filename from path
        import os

        filename = os.path.basename(file_path) if file_path else f"session_{session_id}_report.{file_type}"

        return DownloadFileResult(file_path=file_path, file_type=file_type, filename=filename)
