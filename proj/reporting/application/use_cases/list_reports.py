"""Application use-case: list reports with filtering and pagination.

This use-case provides admin access to all reports with optional filters.
"""
from typing import Any, Optional
from dataclasses import dataclass

from reporting.domain.ports import ReportRepositoryPort
from reporting.domain.exceptions import UnauthorizedReportAccessError


@dataclass
class ReportListItem:
    report_id: int
    session_id: int
    session_name: str
    generated_by: str
    generated_date: str
    export_status: str  # "exported" | "not_exported"
    file_type: Optional[str]


@dataclass
class PaginationInfo:
    current_page: int
    total_pages: int
    total_reports: int
    page_size: int


@dataclass
class ListReportsResult:
    reports: list[ReportListItem]
    pagination: PaginationInfo


class ListReportsUseCase:
    def __init__(self, report_repository: ReportRepositoryPort):
        self.repo = report_repository

    def execute(
        self,
        requested_by: Any,
        session_id: Optional[int] = None,
        user_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ListReportsResult:
        # permission check: admin only
        role = requested_by.get("role") if isinstance(requested_by, dict) else getattr(requested_by, "role", None)
        if role != "admin":
            raise UnauthorizedReportAccessError("This endpoint is restricted to administrators")

        # For now, return empty result as repository method not implemented
        # TODO: Implement repo.list_reports() with filters and pagination
        return ListReportsResult(
            reports=[],
            pagination=PaginationInfo(
                current_page=page,
                total_pages=0,
                total_reports=0,
                page_size=page_size,
            ),
        )
