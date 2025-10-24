"""Excel exporter stub.

This is a minimal placeholder. For real implementations prefer openpyxl
or xlsxwriter and stream rows to avoid high memory usage.
"""
from typing import Iterable, Mapping


def write_excel(path: str, rows: Iterable[Mapping[str, object]]) -> None:
    """Write rows to an Excel file at `path`.

    Placeholder implementation: raise NotImplementedError so callers are
    aware this is a stub.
    """
    raise NotImplementedError("Excel export not implemented; use csv_exporter or implement write_excel")
