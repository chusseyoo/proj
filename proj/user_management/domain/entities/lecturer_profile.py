"""
Domain entity for LecturerProfile.

Pure domain representation of a lecturer profile.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..exceptions import InvalidDepartmentNameError


@dataclass
class LecturerProfile:
    """
    Domain entity representing a lecturer's profile information.
    
    Separate from the User entity to maintain single responsibility.
    """
    
    lecturer_profile_id: Optional[int]
    user_id: int
    department_name: str
    
    def __post_init__(self):
        """Validate invariants."""
        # Department name must not be empty
        if not self.department_name or not self.department_name.strip():
            raise InvalidDepartmentNameError("Department name cannot be empty")
        
        # Normalize department name
        self.department_name = self.department_name.strip()
    
    def update_department(self, new_department: str) -> None:
        """Update department with validation."""
        if not new_department or not new_department.strip():
            raise InvalidDepartmentNameError("Department name cannot be empty")
        self.department_name = new_department.strip()
    
    def __str__(self) -> str:
        # Consistent natural language pattern: "DepartmentName Lecturer"
        # Matches test expectations and aligns with other entity __str__ formats.
        return f"{self.department_name} Lecturer"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, LecturerProfile):
            return False
        return self.lecturer_profile_id == other.lecturer_profile_id if self.lecturer_profile_id else False
    
    def __hash__(self) -> int:
        return hash(self.lecturer_profile_id) if self.lecturer_profile_id else hash(id(self))
