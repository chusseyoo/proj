"""Compute summary statistics for a report.

This module provides a small utility to compute totals and percentages
from a list of student rows. It intentionally avoids any I/O.
"""
from typing import Iterable, Mapping


def compute_statistics(rows: Iterable[Mapping[str, object]]) -> dict:
    """Compute total_students, present_count, absent_count and percentages.

    rows: iterable of dict-like student rows with a `status` key ("Present"|"Absent").
    Returns a dict with keys matching StatisticsDTO (but as primitives).
    """
    total = 0
    present = 0
    for r in rows:
        total += 1
        if r.get("status") == "Present":
            present += 1

    absent = total - present
    present_pct = (present / total * 100.0) if total else 0.0
    absent_pct = (absent / total * 100.0) if total else 0.0

    # diagnostic counts: within_radius / outside_radius based on row diagnostics
    within_radius_count = 0
    outside_radius_count = 0
    for r in rows:
        wr = r.get("within_radius") if isinstance(r, dict) else getattr(r, "within_radius", None)
        if wr is True:
            within_radius_count += 1
        elif wr is False:
            outside_radius_count += 1

    return {
        "total_students": total,
        "present_count": present,
        "present_percentage": round(present_pct, 2),
        "absent_count": absent,
        "absent_percentage": round(absent_pct, 2),
        "within_radius_count": within_radius_count,
        "outside_radius_count": outside_radius_count,
    }
