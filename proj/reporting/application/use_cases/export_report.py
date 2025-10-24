"""Use-case scaffold: export a generated report to CSV/Excel.

Responsibilities:
- validate the report exists and is exportable (not already exported)
- delegate to exporter (CSV/Excel) and storage adapter
- update report metadata in the repository
"""
from typing import Any


class ExportReportUseCase:
    def __init__(self, report_repository: Any, exporter_factory: Any, storage_adapter: Any):
        self.repo = report_repository
        self.exporter_factory = exporter_factory
        self.storage = storage_adapter

    def execute(self, report_id: int, file_type: str, requested_by: Any) -> dict:
        """Export the report and return export metadata (file_path, download_url).

        Raises ReportAlreadyExportedError or UnauthorizedReportAccessError as needed.
        """
        raise NotImplementedError("ExportReportUseCase.execute not implemented")
