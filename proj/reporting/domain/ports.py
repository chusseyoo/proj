"""Domain-level repository protocol (ports) for the reporting bounded context.

This defines the minimal interface the application layer expects from an
infrastructure repository implementation. Keeping it in the domain keeps
the dependency direction clean (application -> domain.ports <- infra).
"""
from typing import Protocol, Any, Iterable, Optional, Dict, List, runtime_checkable


@runtime_checkable
class ReportRepositoryPort(Protocol):
    def get_session(self, session_id: int) -> Optional[Any]:
        """Return a session-like object or None."""

    def get_eligible_students(self, session_id: int) -> Iterable[Any]:
        """Return iterable of student profile dicts/objects for the session."""

    def get_attendance_for_session(self, session_id: int) -> List[Any]:
        """Return raw attendance records for the session."""

    # Notes on expected shapes (informational):
    # - session object: mapping with at least `id`, `owner_id`, `start_time`, `end_time`
    # - student objects: mapping with at least `student_id`, `student_name`, optional email/program/stream
    # - attendance record: mapping with keys `student_id`, `time_recorded` (datetime or ISO string),
    #   `within_radius` (bool), `latitude`, `longitude`, `status`

    def create_report(self, session_id: int, generated_by: int, metadata: Dict[str, Any]) -> Any:
        """Persist a report record and return a domain Report or its id."""

    def get_report(self, report_id: int) -> Optional[Any]:
        """Return a persisted report or None."""

    def get_report_details(self, report_id: int) -> Optional[Dict[str, Any]]:
        """Return payload for export: {session, students, statistics} or None."""

    def update_export_details(self, report_id: int, file_path: str, file_type: str) -> None:
        """Atomically update report record with export metadata."""
