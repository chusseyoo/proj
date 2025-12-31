"""Domain value object for report statistics.

Provides helpers to build statistics from a list of student attendance rows
without tying callers to application-layer DTOs.
"""
from dataclasses import dataclass
from typing import Iterable, Mapping


def compute_statistics_dict(rows: Iterable[Mapping[str, object]]) -> dict:
    total = 0
    present = 0
    for r in rows:
        total += 1
        if r.get("status") == "Present":
            present += 1

    absent = total - present
    present_pct = (present / total * 100.0) if total else 0.0
    absent_pct = (absent / total * 100.0) if total else 0.0

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


@dataclass
class ReportStatistics:
    total_students: int
    present_count: int
    present_percentage: float
    absent_count: int
    absent_percentage: float
    within_radius_count: int
    outside_radius_count: int

    @classmethod
    def from_rows(cls, rows: Iterable[Mapping[str, object]]) -> "ReportStatistics":
        data = compute_statistics_dict(rows)
        return cls(**data)

    def to_dict(self) -> dict:
        return {
            "total_students": self.total_students,
            "present_count": self.present_count,
            "present_percentage": self.present_percentage,
            "absent_count": self.absent_count,
            "absent_percentage": self.absent_percentage,
            "within_radius_count": self.within_radius_count,
            "outside_radius_count": self.outside_radius_count,
        }
