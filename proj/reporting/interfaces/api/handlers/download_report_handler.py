"""Handler for downloading an exported report file."""
import os
from typing import Any, Optional

from reporting.application.use_cases.download_report import (
    DownloadReportUseCase,
    DownloadFileResult,
)
from reporting.infrastructure.di import get_report_repository


def _build_use_case() -> DownloadReportUseCase:
    repo = get_report_repository()
    return DownloadReportUseCase(repo)


class DownloadReportHandler:
    """Handle report file download requests."""

    def __init__(self, download_use_case: Optional[DownloadReportUseCase] = None):
        self.use_case = download_use_case or _build_use_case()

    def handle(self, report_id: int, requested_by: Any) -> DownloadFileResult:
        """Return file metadata needed for download."""
        requester = {
            "id": getattr(requested_by, "id", None),
            "role": getattr(requested_by, "role", None),
        }

        return self.use_case.execute(report_id, requester)

