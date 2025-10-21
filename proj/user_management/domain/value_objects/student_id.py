"""
StudentId value object with format validation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..exceptions import InvalidStudentIdFormatError


@dataclass(frozen=True)
class StudentId:
    """
    Immutable value object representing a validated student ID.
    
    Format: ABC/123456 (3 uppercase letters, slash, 6 digits)
    Always stored in uppercase.
    """
    
    value: str
    
    # Student ID pattern: 3 uppercase letters / 6 digits
    PATTERN = r'^[A-Z]{3}/[0-9]{6}$'
    
    def __post_init__(self):
        """Validate student ID format and normalize to uppercase."""
        if not self.value:
            raise ValueError("Student ID cannot be empty")
        
        # Normalize to uppercase
        normalized = self.value.upper().strip()
        object.__setattr__(self, 'value', normalized)
        
        # Validate format
        if not re.match(self.PATTERN, normalized):
            raise InvalidStudentIdFormatError(self.value)
    
    def __str__(self) -> str:
        return self.value
    
    def __eq__(self, other) -> bool:
        if isinstance(other, StudentId):
            return self.value == other.value
        return False
    
    def __hash__(self) -> int:
        return hash(self.value)
    
    @property
    def program_code(self) -> str:
        """Extract program code (first 3 letters)."""
        return self.value[:3]
    
    @property
    def number(self) -> str:
        """Extract number part (6 digits after slash)."""
        return self.value[4:] if '/' in self.value else ''
    
    @classmethod
    def validate_format(cls, value: str) -> bool:
        """Check if a string matches the student ID format."""
        if not value:
            return False
        normalized = value.upper().strip()
        return bool(re.match(cls.PATTERN, normalized))
