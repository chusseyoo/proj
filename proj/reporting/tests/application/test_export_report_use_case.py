"""Tests for ExportReportUseCase."""
from reporting.application.use_cases.export_report import ExportReportUseCase
from reporting.domain.entities.report import Report


class FakeExporter:
    def export_bytes(self, payload):
        students = payload.get("students", [])
        rows = [f"{s.get('student_id')},{s.get('status')}" for s in students]
        return "\n".join(rows).encode("utf-8")


class FakeExporterFactory:
    def get_exporter(self, file_type):
        return FakeExporter()


class FakeStorage:
    def __init__(self):
        self.saved = {}

    def save_export(self, content_bytes, filename_hint):
        path = f"/tmp/{filename_hint}"
        self.saved[path] = content_bytes
        return path


class FakeRepo:
    def __init__(self):
        self.report = Report(id=2, session_id=10, generated_by=1)
        self.updated = None

    def get_report(self, report_id):
        return self.report if report_id == self.report.id else None

    def get_report_details(self, report_id):
        if report_id != self.report.id:
            return None
        return {"session": {"id": 10}, "students": [{"student_id": "s1", "status": "Present"}], "statistics": {"total_students": 1, "present_count": 1}}

    def update_export_details(self, report_id, file_path, file_type):
        self.updated = (report_id, file_path, file_type)


def test_export_report_happy_path():
    repo = FakeRepo()
    factory = FakeExporterFactory()
    storage = FakeStorage()
    uc = ExportReportUseCase(repo, factory, storage)

    result = uc.execute(2, file_type="csv", requested_by={"id": 1, "role": "admin"})
    assert result["file_type"] == "csv"
    assert result["file_path"].startswith("/tmp/")
    assert repo.updated is not None


def test_export_report_missing_report():
    """If the report does not exist, raise ValueError."""
    class RepoNoReport(FakeRepo):
        def get_report(self, report_id):
            return None

    repo = RepoNoReport()
    factory = FakeExporterFactory()
    storage = FakeStorage()
    uc = ExportReportUseCase(repo, factory, storage)

    import pytest

    with pytest.raises(ValueError) as exc:
        uc.execute(999, file_type="csv", requested_by={"id": 1, "role": "admin"})

    assert "report 999 not found" in str(exc.value)


def test_export_report_already_exported():
    """If the report already has a file_path, exporting should be blocked."""
    class RepoAlreadyExported(FakeRepo):
        def __init__(self):
            super().__init__()
            self.report.file_path = "/tmp/already"

    repo = RepoAlreadyExported()
    factory = FakeExporterFactory()
    storage = FakeStorage()
    uc = ExportReportUseCase(repo, factory, storage)

    import pytest

    with pytest.raises(ValueError) as exc:
        uc.execute(2, file_type="csv", requested_by={"id": 1, "role": "admin"})

    assert "report already exported" in str(exc.value)


def test_export_report_storage_failure():
    """If storage.save_export raises, ensure exception propagates and repo.update_export_details is not called."""
    class BrokenStorage(FakeStorage):
        def save_export(self, content_bytes, filename_hint):
            raise IOError("disk full")

    repo = FakeRepo()
    factory = FakeExporterFactory()
    storage = BrokenStorage()
    uc = ExportReportUseCase(repo, factory, storage)

    import pytest

    with pytest.raises(IOError) as exc:
        uc.execute(2, file_type="csv", requested_by={"id": 1, "role": "admin"})

    assert "disk full" in str(exc.value)
    assert repo.updated is None
