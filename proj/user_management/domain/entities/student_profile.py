"""
Domain entity for StudentProfile.

Pure domain representation of a student profile.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..value_objects import StudentId
from ..exceptions import InvalidYearError


@dataclass
class StudentProfile:
    """
    Domain entity representing a student's profile information.
    
    Separate from the User entity to maintain single responsibility.
    """
    
    student_profile_id: Optional[int]
    student_id: StudentId
    user_id: int
    program_id: int
    stream_id: Optional[int]
    year_of_study: int
    # qr_code_data is derived from student_id; optional at construction to avoid duplication
    qr_code_data: Optional[str] = None
    
    def __post_init__(self):
        """Validate invariants and derive qr_code_data if not provided.

        This centralizes the qr_code_data derivation to the domain layer so
        application/services code does not need to duplicate assignment. The
        invariant (qr_code_data == student_id) is enforced here.
        """
        # Year must be between 1 and 4
        if not (1 <= self.year_of_study <= 4):
            raise InvalidYearError(self.year_of_study)

        # Derive qr_code_data if missing
        if self.qr_code_data is None:
            self.qr_code_data = str(self.student_id)
        elif self.qr_code_data != str(self.student_id):
            raise ValueError("QR code data must match student ID")
    
    @property
    def program_code(self) -> str:
        """Extract program code from student ID."""
        return self.student_id.program_code
    
    def update_year(self, new_year: int) -> None:
        """Update year of study with validation."""
        if not (1 <= new_year <= 4):
            raise InvalidYearError(new_year)
        self.year_of_study = new_year
    
    def update_stream(self, new_stream_id: Optional[int]) -> None:
        """Update stream assignment."""
        self.stream_id = new_stream_id
    
    def __str__(self) -> str:
        return f"Student {self.student_id}"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, StudentProfile):
            return False
        return self.student_profile_id == other.student_profile_id if self.student_profile_id else False
    
    def __hash__(self) -> int:
        return hash(self.student_profile_id) if self.student_profile_id else hash(id(self))
