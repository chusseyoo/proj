"""Minimal CSV exporter scaffold for reporting.

Produces CSV with header and rows. In production this should handle
streaming, large datasets, proper quoting and UTF-8 encoding.
"""
import csv
from typing import Iterable, Mapping


CSV_HEADER = [
    "student_id",
    "student_name",
    "email",
    "program",
    "stream",
    "status",
    "time_recorded",
    "within_radius",
    "latitude",
    "longitude",
]


def write_csv(path: str, rows: Iterable[Mapping[str, object]]) -> None:
    """Write rows (dict-like) to CSV file at `path`.

    Each row should contain keys matching CSV_HEADER. This is a minimal
    implementation; callers must ensure path exists and handle errors.
    """
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_HEADER)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
