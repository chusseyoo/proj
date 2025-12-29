"""Django ORM models for attendance_recording infrastructure layer.

Implements the `Attendance` model according to the docs:
- Immutable records (no update API)
- Unique per (student_profile, session)
- Precise GPS coordinates and within-radius flag
"""

from __future__ import annotations

from django.db import models


class Attendance(models.Model):
    """Attendance record for a student in a session.

    Fields align with proj_docs attendance-recording specs.
    """

    attendance_id = models.AutoField(primary_key=True)

    # Foreign keys across contexts
    student_profile = models.ForeignKey(
        "user_management.StudentProfile",
        on_delete=models.CASCADE,  # cascade deletion as per docs
        related_name="attendance_records",
    )
    session = models.ForeignKey(
        "session_management.Session",
        on_delete=models.CASCADE,  # cascade deletion as per docs
        related_name="attendance_records",
    )

    # Server-side timestamp when attendance is recorded
    time_recorded = models.DateTimeField(auto_now_add=True)

    # GPS coordinates (precision consistent with docs)
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)

    class Status(models.TextChoices):
        PRESENT = "present", "present"
        LATE = "late", "late"

    status = models.CharField(max_length=20, choices=Status.choices)
    is_within_radius = models.BooleanField(default=False)

    class Meta:
        db_table = "attendance"
        app_label = "attendance_recording"
        # One record per student per session
        constraints = [
            models.UniqueConstraint(
                fields=["student_profile", "session"],
                name="uq_attendance_student_session",
            ),
            models.CheckConstraint(
                condition=models.Q(latitude__gte=-90) & models.Q(latitude__lte=90),
                name="ck_att_lat_range",
            ),
            models.CheckConstraint(
                condition=models.Q(longitude__gte=-180) & models.Q(longitude__lte=180),
                name="ck_att_lon_range",
            ),
        ]
        indexes = [
            models.Index(fields=["student_profile"], name="idx_att_student"),
            models.Index(fields=["session"], name="idx_att_session"),
            models.Index(fields=["status"], name="idx_att_status"),
            models.Index(fields=["time_recorded"], name="idx_att_time_recorded"),
        ]

    def __str__(self) -> str:  # pragma: no cover - trivial
        student_name = getattr(self.student_profile.user, 'full_name', 'Unknown') if hasattr(self, 'student_profile') else 'Unknown'
        session_info = getattr(self, 'session', 'Unknown')
        return f"{student_name} - {self.status} - {session_info}"

    def is_late(self) -> bool:
        """Check if status is late."""
        return self.status == self.Status.LATE

    def is_present(self) -> bool:
        """Check if status is present."""
        return self.status == self.Status.PRESENT

    def get_distance_from_session(self) -> float:
        """Recalculate distance from session location using Haversine formula.
        
        Returns distance in meters. Used for verification and debugging.
        """
        from math import radians, cos, sin, asin, sqrt
        
        if not hasattr(self, 'session'):
            return 0.0
        
        # Haversine formula
        lat1, lon1 = float(self.latitude), float(self.longitude)
        lat2, lon2 = float(self.session.latitude), float(self.session.longitude)
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371000  # Earth radius in meters
        return c * r

    def was_on_time(self) -> bool:
        """Check if attendance was marked early in session window.
        
        Helps distinguish 'present' from 'late but within time'.
        """
        if not hasattr(self, 'session'):
            return False
        # Consider on-time if marked in first half of session
        session_duration = (self.session.time_ended - self.session.time_created).total_seconds()
        time_since_start = (self.time_recorded - self.session.time_created).total_seconds()
        return time_since_start < session_duration / 2
