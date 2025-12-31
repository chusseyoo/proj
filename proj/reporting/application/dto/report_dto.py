"""DTOs for reporting application use-cases.

These are simple dataclasses that represent the shape of data passed
between application/use-cases, handlers and exporters.
"""
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class StudentRowDTO:
    student_id: str
    student_name: str
    email: Optional[str]
    program: Optional[str]
    stream: Optional[str]
    status: str  # "Present" or "Absent"
    time_recorded: Optional[str]
    within_radius: Optional[bool]
    latitude: Optional[str]
    longitude: Optional[str]


@dataclass
class StatisticsDTO:
    total_students: int
    present_count: int
    present_percentage: float
    absent_count: int
    absent_percentage: float
    within_radius_count: Optional[int] = None  # diagnostic
    outside_radius_count: Optional[int] = None  # diagnostic


@dataclass
class ReportDTO:
    report_id: Optional[int]
    session: dict
    statistics: StatisticsDTO
    students: List[StudentRowDTO]
    generated_date: Optional[str]
    generated_by: Optional[str]
    export_status: str  # "not_exported" | "exported"


@dataclass
class ExportResultDTO:
    """Result of exporting a report to file."""

    report_id: int
    file_path: str
    file_type: str
    download_url: str
    generated_date: Optional[str] = None


@dataclass
class DownloadFileDTO:
    """Information needed to serve a file download."""

    file_path: str
    file_type: str
    filename: str
    content_type: str

    @classmethod
    def from_export_result(cls, file_path: str, file_type: str, filename: str) -> "DownloadFileDTO":
        """Create from export result with appropriate content type."""
        content_type = "text/csv" if file_type == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return cls(file_path=file_path, file_type=file_type, filename=filename, content_type=content_type)
