"""Compute summary statistics for a report (domain-level helper).

This module keeps backward compatibility by returning plain dictionaries
while also exposing a dataclass for richer use in the domain layer.
"""
from typing import Iterable, Mapping

from reporting.domain.value_objects.report_statistics import ReportStatistics, compute_statistics_dict


def compute_statistics(rows: Iterable[Mapping[str, object]]) -> dict:
    """Return statistics as primitives (legacy callers)."""
    return compute_statistics_dict(rows)


def compute_statistics_obj(rows: Iterable[Mapping[str, object]]) -> ReportStatistics:
    """Return statistics as a `ReportStatistics` value object."""
    return ReportStatistics.from_rows(rows)
