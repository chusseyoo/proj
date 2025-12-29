"""Value objects for attendance recording domain.

These are immutable domain objects that encapsulate validation and business logic
for key domain concepts.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StudentProfileID:
    """Student profile identifier (foreign key to StudentProfile).
    
    Represents the student_profile_id integer used to reference StudentProfile
    from the User Management context.
    
    Example: StudentProfileID(123)
    """

    value: int

    def __post_init__(self) -> None:
        """Validate that ID is a positive integer."""
        if not isinstance(self.value, int) or self.value <= 0:
            raise ValueError(f"StudentProfileID must be positive integer, got {self.value}")

    def __int__(self) -> int:
        """Allow conversion to int."""
        return self.value


@dataclass(frozen=True)
class GPSCoordinate:
    """GPS coordinate value object (latitude/longitude pair).
    
    Represents a physical location using decimal degrees.
    Validates coordinate ranges per WGS84 standard.
    
    Examples:
        GPSCoordinate(-1.28333412, 36.81666588)  # Nairobi, Kenya
    """

    latitude: float
    longitude: float

    def __post_init__(self):
        """Validate coordinate ranges."""
        if not (-90 <= self.latitude <= 90):
            raise ValueError(
                f"Latitude must be between -90 and 90, got {self.latitude}"
            )

        if not (-180 <= self.longitude <= 180):
            raise ValueError(
                f"Longitude must be between -180 and 180, got {self.longitude}"
            )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "latitude": float(self.latitude),
            "longitude": float(self.longitude),
        }


@dataclass(frozen=True)
class SessionTimeWindow:
    """Session time window value object.
    
    Represents the active period during which students can mark attendance.
    Uses datetime objects for precise time handling.
    
    Methods:
        is_active(current_time): Check if current time is within window
        is_started(current_time): Check if session has begun
        is_ended(current_time): Check if session has concluded
    
    Examples:
        window = SessionTimeWindow(
            start_time=datetime(2025, 10, 25, 8, 0),
            end_time=datetime(2025, 10, 25, 10, 0),
        )
    """

    start_time: datetime
    end_time: datetime

    def __post_init__(self):
        """Validate time window ordering."""
        if self.end_time <= self.start_time:
            raise ValueError(
                f"End time must be after start time, "
                f"got {self.start_time} to {self.end_time}"
            )

    def is_active(self, current_time: datetime) -> bool:
        """Check if current time is within session window (inclusive)."""
        return self.start_time <= current_time <= self.end_time

    def is_started(self, current_time: datetime) -> bool:
        """Check if session has started."""
        return current_time >= self.start_time

    def is_ended(self, current_time: datetime) -> bool:
        """Check if session has ended."""
        return current_time > self.end_time

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
        }
