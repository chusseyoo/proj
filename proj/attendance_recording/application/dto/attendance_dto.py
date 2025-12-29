"""Application DTOs for attendance recording."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from attendance_recording.domain.entities.attendance import Attendance


@dataclass
class AttendanceDTO:
    """Data transfer object for Attendance entity."""

    attendance_id: int
    student_profile_id: int
    session_id: int
    status: str
    is_within_radius: bool
    time_recorded: datetime
    latitude: float
    longitude: float

    @staticmethod
    def from_entity(attendance: Attendance) -> "AttendanceDTO":
        """Map domain entity to DTO."""
        return AttendanceDTO(
            attendance_id=attendance.attendance_id or 0,
            student_profile_id=attendance.student_id,
            session_id=attendance.session_id,
            status=attendance.status,
            is_within_radius=attendance.is_within_radius,
            time_recorded=attendance.time_recorded,
            latitude=attendance.latitude,
            longitude=attendance.longitude,
        )

    def to_dict(self) -> dict:
        """Serialize DTO to primitive dict for responses."""
        return {
            "attendance_id": self.attendance_id,
            "student_profile_id": self.student_profile_id,
            "session_id": self.session_id,
            "status": self.status,
            "is_within_radius": self.is_within_radius,
            "time_recorded": self.time_recorded,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }
