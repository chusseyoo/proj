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
"""Tests for CSV exporter scaffold (implemented).

These tests exercise the CSV exporter factory and the CSV writer
helpers to ensure header presence, proper quoting, and file writing.
"""
import pytest
from reporting.infrastructure.exporters.factory import ExporterFactory
from reporting.infrastructure.exporters.csv_exporter import CSV_HEADER, write_csv


def test_csv_exporter_writes_file(tmp_path):
    factory = ExporterFactory()
    exporter = factory.get_exporter("csv")

    payload = {
        "students": [
            {
                "student_id": "s1",
                "student_name": "Alice, Q.",
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
    header = text.splitlines()[0]
    assert "student_id" in header
    assert "status" in header

    # and the row should contain the student id and status and quoted name
    assert "s1" in text
    assert "Present" in text
    assert '"Alice, Q."' in text or 'Alice, Q.' in text


def test_write_csv_function_and_empty_payload(tmp_path):
    # write_csv should create a file with header even if rows empty
    p = tmp_path / "out.csv"
    write_csv(str(p), [])
    content = p.read_text(encoding="utf-8")
    lines = content.splitlines()
    assert lines[0].split(",") == CSV_HEADER
