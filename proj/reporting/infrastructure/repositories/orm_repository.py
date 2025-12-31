"""Complete ORM-backed repository implementing the domain port for reports.

This repository integrates with cross-context Django models (Session, Attendance,
StudentProfile) to provide all data needed for report generation.
"""
from typing import Any, Optional, Dict, List
from datetime import datetime

from reporting.models import Report
from reporting.domain.exceptions.core import SessionNotFoundError


class OrmReportRepository:
    """ORM repository implementing ReportRepositoryPort.

    Integrates with:
    - session_management.Session (cross-context)
    - attendance_recording.Attendance (cross-context)
    - user_management.StudentProfile (cross-context)
    """

    def create_report(self, session_id: int, generated_by: int, metadata: Dict[str, Any]) -> Report:
        """Create new report metadata record."""
        r = Report.objects.create(
            session_id=session_id,
            generated_by=generated_by,
            metadata=metadata
        )
        return r

    def get_report(self, report_id: int) -> Optional[Report]:
        """Get report by ID."""
        try:
            return Report.objects.get(pk=report_id)
        except Report.DoesNotExist:
            return None

    def update_export_details(self, report_id: int, file_path: str, file_type: str) -> None:
        """Update report with export file metadata (atomic with row locking)."""
        from django.db import transaction

        with transaction.atomic():
            try:
                r = Report.objects.select_for_update().get(pk=report_id)
            except Report.DoesNotExist:
                from reporting.domain.exceptions.core import ReportNotFoundError
                raise ReportNotFoundError(f"report {report_id} not found")

            if r.file_path:
                from reporting.domain.exceptions.core import ReportAlreadyExportedError
                raise ReportAlreadyExportedError("report already exported")

            r.file_path = file_path
            r.file_type = file_type
            r.save(update_fields=["file_path", "file_type"])

    def get_report_details(self, report_id: int) -> Optional[Dict[str, Any]]:
        """Get report details including session and stored metadata."""
        r = self.get_report(report_id)
        if not r:
            return None

        return {
            "session": {"id": r.session_id},
            "students": r.metadata.get("students", []) if isinstance(r.metadata, dict) else [],
            "statistics": r.metadata.get("statistics", {}) if isinstance(r.metadata, dict) else {},
        }

    # ====================
    # Cross-Context Integration
    # ====================

    def get_session(self, session_id: int) -> Any:
        """Get session from session_management context."""
        from session_management.infrastructure.orm.django_models import Session

        try:
            session = Session.objects.select_related(
                'program', 'course', 'lecturer__user', 'stream'
            ).get(pk=session_id)
            return session
        except Session.DoesNotExist:
            return None

    def get_eligible_students(self, session_id: int) -> List[Dict[str, Any]]:
        """Get all students eligible for session (by program/stream).
        
        Returns list of dicts with student details.
        """
        from user_management.infrastructure.orm.django_models import StudentProfile

        session = self.get_session(session_id)
        if not session:
            raise SessionNotFoundError(f"session {session_id} not found")

        # Query students by program and stream (if specified)
        qs = StudentProfile.objects.select_related('user', 'program', 'stream')
        qs = qs.filter(program=session.program)

        if session.stream:
            qs = qs.filter(stream=session.stream)

        # Convert to dict format expected by domain layer
        students = []
        for sp in qs:
            students.append({
                "student_id": sp.student_id,
                "student_name": sp.user.get_full_name() if hasattr(sp.user, 'get_full_name') else f"{sp.user.first_name} {sp.user.last_name}",
                "email": sp.user.email,
                "program": sp.program.name if sp.program else "",
                "stream": sp.stream.name if sp.stream else "",
            })

        return students

    def get_attendance_for_session(self, session_id: int) -> List[Dict[str, Any]]:
        """Get all attendance records for session.
        
        Returns list of dicts with attendance details.
        """
        from attendance_recording.infrastructure.orm.django_models import Attendance

        qs = Attendance.objects.filter(session_id=session_id).select_related(
            'student_profile__user'
        )

        # Convert to dict format expected by domain layer
        attendance_records = []
        for att in qs:
            attendance_records.append({
                "student_id": att.student_profile.student_id,
                "time_recorded": att.time_recorded,
                "within_radius": att.is_within_radius,
                "latitude": str(att.latitude),
                "longitude": str(att.longitude),
            })

        return attendance_records
