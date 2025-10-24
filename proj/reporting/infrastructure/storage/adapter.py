import os
import tempfile
import datetime
from typing import Optional

from django.conf import settings


class FilesystemStorageAdapter:
    """Save exported bytes under MEDIA_ROOT/reports/<year>/<month>/ and return final path."""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or getattr(settings, "MEDIA_ROOT", "/tmp")

    def save_export(self, content_bytes: bytes, filename_hint: str) -> str:
        now = datetime.datetime.utcnow()
        year = now.year
        month = now.month
        dir_path = os.path.join(self.base_dir, "reports", str(year), f"{month:02d}")
        os.makedirs(dir_path, exist_ok=True)

        # write to a temp file then atomically move into place
        fd, tmp_path = tempfile.mkstemp(prefix="export_", dir=dir_path)
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(content_bytes)

            final_path = os.path.join(dir_path, filename_hint)
            os.replace(tmp_path, final_path)
            return final_path
        finally:
            # ensure temp cleaned if something failed
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
