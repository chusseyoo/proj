from typing import Any, Optional, Dict

from reporting.models import Report


class OrmReportRepository:
    """Minimal ORM-backed repository implementing the domain port for reports.

    Note: This implementation focuses on persisting report metadata and
    export details. Session/attendance/eligible students access should be
    implemented by importing the project's Session/Attendance models and
    performing the appropriate queries.
    """

    def create_report(self, session_id: int, generated_by: int, metadata: Dict[str, Any]) -> Report:
        r = Report.objects.create(session_id=session_id, generated_by=generated_by, metadata=metadata)
        return r

    def get_report(self, report_id: int) -> Optional[Report]:
        try:
            return Report.objects.get(pk=report_id)
        except Report.DoesNotExist:
            return None

    def update_export_details(self, report_id: int, file_path: str, file_type: str) -> None:
        r = self.get_report(report_id)
        if r is None:
            raise ValueError(f"report {report_id} not found")
        if r.file_path:
            raise ValueError("report already exported")
        r.file_path = file_path
        r.file_type = file_type
        r.save(update_fields=["file_path", "file_type"])

    def get_report_details(self, report_id: int) -> Optional[Dict[str, Any]]:
        r = self.get_report(report_id)
        if not r:
            return None
        # Basic payload: caller may prefer richer session/student shapes
        return {
            "session": {"id": r.session_id},
            "students": r.metadata.get("students", []) if isinstance(r.metadata, dict) else [],
            "statistics": r.metadata.get("statistics", {}) if isinstance(r.metadata, dict) else {},
        }

    # The following methods require knowledge of project models (Session, Attendance, Student).
    def get_session(self, session_id: int) -> Any:
        raise NotImplementedError("Implement session lookup using the project's Session model")

    def get_eligible_students(self, session_id: int):
        raise NotImplementedError("Implement eligible student lookup using project models")

    def get_attendance_for_session(self, session_id: int):
        raise NotImplementedError("Implement attendance lookup using project models")
