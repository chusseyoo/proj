"""CQRS-style command and query objects for reporting application layer.

Commands represent write operations (generate, export).
Queries represent read operations (view, list, download).
"""
from dataclasses import dataclass
from typing import Any, Optional


# ============================================================================
# COMMANDS (Write Operations)
# ============================================================================


@dataclass
class GenerateReportCommand:
    """Command to generate a new attendance report for a session."""

    session_id: int
    requested_by: Any  # User dict or object with id and role


@dataclass
class ExportReportCommand:
    """Command to export an existing report to CSV or Excel."""

    report_id: int
    file_type: str  # "csv" or "excel"
    requested_by: Any


# ============================================================================
# QUERIES (Read Operations)
# ============================================================================


@dataclass
class ViewReportQuery:
    """Query to view an existing report's current data."""

    report_id: int
    requested_by: Any


@dataclass
class ListReportsQuery:
    """Query to list reports with filters and pagination (admin only)."""

    requested_by: Any
    session_id: Optional[int] = None
    user_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    page: int = 1
    page_size: int = 20


@dataclass
class DownloadReportQuery:
    """Query to get download information for an exported report."""

    report_id: int
    requested_by: Any
