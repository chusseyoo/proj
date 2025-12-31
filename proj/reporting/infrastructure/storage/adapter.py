import os
import tempfile
from typing import Optional
from datetime import datetime

from django.conf import settings
try:
    from django.utils import timezone
except Exception:
    timezone = None

from .utils import make_reports_path, write_file_atomic, generate_report_filename


class FilesystemStorageAdapter:
    """Save exported bytes under MEDIA_ROOT/reports/<year>/<month>/ and return final path.
    
    Organizes export files by year/month folders with timestamp-based filenames
    to prevent overwrites and enable easy cleanup.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or getattr(settings, "MEDIA_ROOT", "/tmp")

    def save_export(self, content_bytes: bytes, filename_hint: str) -> str:
        """Save export file to organized directory structure.
        
        Creates: {MEDIA_ROOT}/reports/{YYYY}/{MM}/{filename_hint}
        Atomically moves temp file to final location.
        
        Args:
            content_bytes: File content as bytes
            filename_hint: Suggested filename (e.g., "session_10_20251230.csv")
        
        Returns:
            Absolute path to saved file
        
        Raises:
            OSError: If directory creation or file write fails
        """
        # Get current time (prefer Django timezone for consistency)
        if timezone is not None:
            try:
                now = timezone.now()
            except Exception:
                now = datetime.datetime.now(datetime.timezone.utc)
        else:
            now = datetime.datetime.now(datetime.timezone.utc)
        
        year = now.year
        month = now.month
        
        # Create year/month directory
        dir_path = make_reports_path(self.base_dir, year, month)
        
        # Create temp file in target directory to ensure same filesystem
        fd, tmp_path = tempfile.mkstemp(prefix="export_", dir=dir_path)
        try:
            # Write content to temp file
            with os.fdopen(fd, "wb") as fh:
                fh.write(content_bytes)

            # Atomically move to final location
            final_path = os.path.join(dir_path, filename_hint)
            write_file_atomic(tmp_path, final_path)
            return final_path
        finally:
            # Cleanup temp file if something failed
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
