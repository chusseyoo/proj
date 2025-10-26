from reporting.infrastructure.exporters.factory import ExporterFactory


def test_csv_exporter_produces_header_and_rows():
    factory = ExporterFactory()
    exporter = factory.get_exporter("csv")

    payload = {
        "students": [
            {
                "student_id": "s1",
                "student_name": "Alice",
                "email": "a@example.com",
                "program": "CS",
                "stream": "FT",
                "status": "Present",
                "time_recorded": "2025-10-19T08:05:00",
                "within_radius": True,
                "latitude": "1",
                "longitude": "2",
            }
        ]
    }

    data = exporter.export_bytes(payload)
    text = data.decode("utf-8")

    # header should include student_id and status
    assert "student_id" in text.splitlines()[0]
    assert "status" in text.splitlines()[0]

    # and the row should contain the student id and status
    assert "s1" in text
    assert "Present" in text
"""Tests for CSV exporter scaffold (placeholder)."""
import pytest


def test_csv_exporter_writes_file(tmp_path):
    pytest.skip("Implement CSV exporter tests")
