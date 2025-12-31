"""Domain value object representing a student's attendance row in a report.

This lives in the domain layer to avoid coupling aggregation logic to the
application DTOs. Application serializers/DTOs can adapt from this shape.
"""
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class StudentAttendanceRow:
    student_id: str
    student_name: Optional[str]
    email: Optional[str]
    program: Optional[str]
    stream: Optional[str]
    status: str  # "Present" or "Absent"
    time_recorded: Optional[str]
    within_radius: Optional[bool]
    latitude: Optional[str]
    longitude: Optional[str]

    def to_dict(self) -> dict:
        """Serialize to a plain dict for storage/export."""
        return asdict(self)
