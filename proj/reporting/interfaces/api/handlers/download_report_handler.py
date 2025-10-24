"""Handler scaffold for downloading an exported report file."""
from typing import Any


class DownloadReportHandler:
    def __init__(self, storage_adapter: Any, report_repository: Any):
        self.storage = storage_adapter
        self.repo = report_repository

    def handle(self, request: Any, report_id: int) -> Any:
        """Return a response or file-like object for download.

        Should check permissions and file existence.
        """
        raise NotImplementedError("DownloadReportHandler.handle not implemented")
