"""Storage utility functions for filesystem operations."""
import os
from datetime import datetime
from typing import Optional


def make_reports_path(base_dir: str, year: int, month: int) -> str:
    """Create organized directory structure for reports.
    
    Creates: {base_dir}/{year}/{month:02d}/
    Example: /media/reports/2025/12/
    
    Args:
        base_dir: Root directory for reports
        year: Year (e.g., 2025)
        month: Month (1-12)
    
    Returns:
        Path to year/month directory (created if needed)
    """
    path = os.path.join(base_dir, str(year), f"{month:02d}")
    os.makedirs(path, exist_ok=True)
    return path


def generate_report_filename(session_id: int, file_type: str, timestamp: Optional[datetime] = None) -> str:
    """Generate standardized report filename.
    
    Format: session_{session_id}_{YYYYMMDDHHMMSS}.{csv|xlsx}
    Example: session_10_20251230143022.csv
    
    Args:
        session_id: Session ID for the report
        file_type: Export format ("csv" or "excel")
        timestamp: Optional timestamp (uses now() if not provided)
    
    Returns:
        Filename (without directory path)
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    if file_type == "excel":
        ext = "xlsx"
    else:
        ext = file_type  # "csv" → "csv"
    
    ts_str = timestamp.strftime("%Y%m%d%H%M%S")
    return f"session_{session_id}_{ts_str}.{ext}"


def write_file_atomic(tmp_path: str, final_path: str) -> None:
    """Atomically move temporary file to final location.
    
    Uses os.replace() for atomic operation on POSIX systems.
    Ensures partial writes don't leave corrupted files.
    
    Args:
        tmp_path: Temporary file location
        final_path: Target location
    
    Raises:
        OSError: If file operation fails
    """
    os.replace(tmp_path, final_path)


def get_safe_export_path(base_dir: str, session_id: int, file_type: str) -> str:
    """Generate full path for export file with year/month organization.
    
    Example:
        /media/reports/2025/12/session_10_20251230143022.csv
    
    Args:
        base_dir: Root reports directory
        session_id: Session ID
        file_type: Export format
    
    Returns:
        Full path to export file
    """
    now = datetime.now()
    dir_path = make_reports_path(base_dir, now.year, now.month)
    filename = generate_report_filename(session_id, file_type, now)
    return os.path.join(dir_path, filename)
