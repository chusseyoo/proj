"""HTTP handler glue for generating a report.

This module should be used by a DRF view or Django view to call the
GenerateReportUseCase and translate domain/application exceptions into
HTTP responses.
"""
from typing import Any


class GenerateReportHandler:
    """Thin handler that wraps the GenerateReport use-case."""

    def __init__(self, generate_report_use_case: Any):
        self.use_case = generate_report_use_case

    def handle(self, request: Any, session_id: int) -> Any:
        """Execute the use-case and return a tuple (status_code, payload).

        The real implementation should return a DRF Response or raise
        appropriate exceptions (PermissionDenied, NotFound, etc.).
        """
        # TODO: implement calling use_case.execute and formatting response
        raise NotImplementedError("GenerateReportHandler.handle not implemented")
