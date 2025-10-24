"""Handler scaffold for exporting a generated report."""
from typing import Any


class ExportReportHandler:
    def __init__(self, export_use_case: Any):
        self.use_case = export_use_case

    def handle(self, request: Any, report_id: int, payload: dict) -> Any:
        """Validate request and invoke export use-case.

        Expected to return (status_code, payload) or raise exceptions.
        """
        raise NotImplementedError("ExportReportHandler.handle not implemented")
