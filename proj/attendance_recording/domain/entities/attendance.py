"""Attendance domain entity.

Core entity representing a single attendance record for a student at a session.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Attendance:
    """Attendance entity - immutable aggregate root.
    
    Represents a student marking attendance for a session with location validation.
    All fields are set at creation and immutable (frozen).
    
    Domain Constraints:
    - Student ID must be positive
    - Session ID must be positive
    - Latitude: -90 to 90
    - Longitude: -180 to 180
    - Status: "present" or "late"
    - One attendance per student per session (enforced at repository/DB level)
    """
    
    attendance_id: Optional[int]
    student_id: int  # FK to StudentProfile.student_profile_id (integer)
    session_id: int
    time_recorded: datetime
    latitude: float
    longitude: float
    status: str  # "present" or "late" (CharField choices in ORM)
    is_within_radius: bool
    
    def __post_init__(self) -> None:
        """Validate attendance data upon creation."""
        # Validate GPS coordinates
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {self.latitude}")
        
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {self.longitude}")
        
        # Validate status
        valid_statuses = ["present", "late"]
        if self.status not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}, got {self.status}")
        
        # Validate IDs are positive
        if self.student_id <= 0:
            raise ValueError(f"student_id must be positive, got {self.student_id}")
        
        if self.session_id <= 0:
            raise ValueError(f"session_id must be positive, got {self.session_id}")
    
    @classmethod
    def create(
        cls,
        student_id: int,
        session_id: int,
        time_recorded: datetime,
        latitude: float,
        longitude: float,
        status: str,
        is_within_radius: bool,
    ) -> "Attendance":
        """Factory method to create new attendance record (without ID).
        
        Used when creating a new attendance record before persistence.
        Repository will assign attendance_id on save.
        
        Args:
            student_id: FK to StudentProfile.student_profile_id
            session_id: FK to Session.session_id
            time_recorded: When attendance was marked (server timestamp)
            latitude: Student's GPS latitude when marking
            longitude: Student's GPS longitude when marking
            status: "present" or "late"
            is_within_radius: Whether within 30m of session location
        
        Returns:
            New Attendance entity with attendance_id=None
        """
        return cls(
            attendance_id=None,
            student_id=student_id,
            session_id=session_id,
            time_recorded=time_recorded,
            latitude=latitude,
            longitude=longitude,
            status=status,
            is_within_radius=is_within_radius,
        )
    
    def to_dict(self) -> dict:
        """Convert attendance to dictionary for serialization."""
        return {
            "attendance_id": self.attendance_id,
            "student_id": self.student_id,
            "session_id": self.session_id,
            "time_recorded": self.time_recorded.isoformat() if isinstance(self.time_recorded, datetime) else self.time_recorded,
            "latitude": float(self.latitude),
            "longitude": float(self.longitude),
            "status": self.status,
            "is_within_radius": self.is_within_radius,
        }
