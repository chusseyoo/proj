"""Django ORM-backed repository for report metadata and helper queries.

This is a scaffold with method signatures and ORM sketch comments. Implement
these methods using the project's Session/Attendance/Student models.
"""
from typing import Any, List, Optional


class ReportRepository:
    """Repository for creating and retrieving report records and helper queries."""

    def create_report(self, session_id: int, generated_by: int, metadata: dict) -> Any:
        """Persist a report record and return it (or its id).

        metadata: arbitrary dict for report header values.
        """
        raise NotImplementedError

    def get_report(self, report_id: int) -> Optional[Any]:
        """Return report record or None."""
        raise NotImplementedError

    def update_export_details(self, report_id: int, file_path: str, file_type: str) -> None:
        """Update a report record with export details (atomic).

        Should raise an error if the report is already exported.
        """
        raise NotImplementedError

    def get_attendance_for_session(self, session_id: int) -> List[Any]:
        """Return raw attendance records for the session (select_related as needed).

        ORM sketch for present_count (Django ORM):

        present_count = (
            Attendance.objects
            .filter(session_id=session_id,
                    time_recorded__gte=session.start_time,
                    time_recorded__lte=session.end_time,
                    within_radius=True)
            .values('student_id')
            .distinct()
            .count()
        )

        Keep diagnostic counts (within_radius_count, outside_radius_count) separately.
        """
        raise NotImplementedError
