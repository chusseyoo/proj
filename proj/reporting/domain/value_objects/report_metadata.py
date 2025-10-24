"""Value objects for report metadata."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ReportMetadata:
    session_id: int
    generated_by: int
    generated_date: Optional[str] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None
