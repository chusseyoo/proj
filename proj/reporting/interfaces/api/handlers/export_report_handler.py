"""Handler for exporting a generated report."""
from typing import Any, Optional

from reporting.application.dto.report_dto import ExportResultDTO
from reporting.application.use_cases.export_report import ExportReportUseCase
from reporting.domain.services.report_access_policy import ReportAccessPolicy
from reporting.infrastructure.di import (
    get_report_repository,
    get_exporter_factory,
    get_storage_adapter,
)


def _build_use_case() -> ExportReportUseCase:
    repo = get_report_repository()
    exporter_factory = get_exporter_factory()
    storage = get_storage_adapter()
    access = ReportAccessPolicy()
    return ExportReportUseCase(repo, exporter_factory, storage, access)


class ExportReportHandler:
    """Handle report export requests."""

    def __init__(self, export_use_case: Optional[ExportReportUseCase] = None):
        self.use_case = export_use_case or _build_use_case()

    def handle(self, report_id: int, file_type: str, requested_by: Any) -> dict[str, Any]:
        """Validate request and invoke export use-case."""
        requester = {
            "id": getattr(requested_by, "id", None),
            "role": getattr(requested_by, "role", None),
        }

        export_dto: ExportResultDTO = self.use_case.execute(report_id, file_type, requester)

        return {
            "report_id": export_dto.report_id,
            "file_type": export_dto.file_type,
            "download_url": export_dto.download_url,
            "generated_date": export_dto.generated_date,
        }

