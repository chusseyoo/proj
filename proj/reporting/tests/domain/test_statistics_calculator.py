"""Tests for statistics calculator diagnostic counts."""
from reporting.domain.services.statistics_calculator import compute_statistics


def test_compute_statistics_with_diagnostics():
    rows = [
        {"student_id": "s1", "status": "Present", "within_radius": True},
        {"student_id": "s2", "status": "Absent", "within_radius": False},
        {"student_id": "s3", "status": "Absent", "within_radius": None},
    ]

    stats = compute_statistics(rows)
    assert stats["total_students"] == 3
    assert stats["present_count"] == 1
    assert stats["absent_count"] == 2
    assert stats["within_radius_count"] == 1
    assert stats["outside_radius_count"] == 1


def test_compute_statistics_empty_rows():
    stats = compute_statistics([])
    assert stats["total_students"] == 0
    assert stats["present_count"] == 0
    assert stats["absent_count"] == 0
    assert stats["within_radius_count"] == 0
    assert stats["outside_radius_count"] == 0
