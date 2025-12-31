"""Exporter factory for CSV and Excel formats."""
import io
import csv
from typing import Any, Mapping

from .csv_exporter import CSV_HEADER


class CsvExporter:
    """CSV exporter producing UTF-8 encoded bytes."""

    def export_bytes(self, payload: Mapping[str, Any]) -> bytes:
        """Produce CSV bytes for the given payload.

        Expected payload shape: {"students": [ {..row..}, ... ], ...}
        """
        rows = payload.get("students", []) or []
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=CSV_HEADER)
        writer.writeheader()
        for r in rows:
            # ensure all header keys exist
            writer.writerow({k: (r.get(k) if isinstance(r, dict) else getattr(r, k, "")) for k in CSV_HEADER})

        return buf.getvalue().encode("utf-8")


class ExporterFactory:
    """Factory to get appropriate exporter by file type."""

    def get_exporter(self, file_type: str):
        """Get exporter instance for given file type.
        
        Supported types:
        - "csv": Returns CsvExporter
        - "excel": Returns ExcelExporter (falls back to CSV if openpyxl unavailable)
        """
        if file_type == "csv":
            return CsvExporter()
        elif file_type == "excel":
            from .excel_exporter import ExcelExporter
            return ExcelExporter()
        raise ValueError(f"unsupported export type: {file_type}")
