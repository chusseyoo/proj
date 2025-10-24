"""Filesystem adapter for saving export files under media/reports."""
import os
from typing import Tuple


def make_reports_path(base_dir: str, year: int, month: int) -> str:
    path = os.path.join(base_dir, str(year), f"{month:02d}")
    os.makedirs(path, exist_ok=True)
    return path


def write_file_atomic(path: str, content_path: str) -> None:
    """Move or write content to final path atomically.

    For scaffold we perform a simple rename; real implementations should
    consider temp files and fsync semantics.
    """
    os.replace(content_path, path)
