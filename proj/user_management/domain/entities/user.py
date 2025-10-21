"""
Domain entity for User.

Pure domain representation of a user, independent of persistence layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from ..value_objects import Email


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "Admin"
    LECTURER = "Lecturer"
    STUDENT = "Student"


@dataclass
class User:
    """
    Domain entity representing a system user.
    
    This is a pure domain entity, separate from the Django ORM model.
    """
    
    user_id: Optional[int]
    first_name: str
    last_name: str
    email: Email
    role: UserRole
    is_active: bool = True
    has_password: bool = False
    date_joined: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate invariants."""
        if not self.first_name or not self.first_name.strip():
            raise ValueError("First name cannot be empty")
        
        if not self.last_name or not self.last_name.strip():
            raise ValueError("Last name cannot be empty")
        
        # Students cannot have passwords
        if self.role == UserRole.STUDENT and self.has_password:
            raise ValueError("Students cannot have passwords")
        
        # Admin and Lecturer must have passwords
        if self.role in (UserRole.ADMIN, UserRole.LECTURER) and not self.has_password:
            raise ValueError("Admin and Lecturer must have passwords")
    
    @property
    def full_name(self) -> str:
        """Return full name."""
        return f"{self.first_name} {self.last_name}"
    
    def is_student(self) -> bool:
        """Check if user is a student."""
        return self.role == UserRole.STUDENT
    
    def is_lecturer(self) -> bool:
        """Check if user is a lecturer."""
        return self.role == UserRole.LECTURER
    
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN
    
    def activate(self) -> None:
        """Activate user account."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Deactivate user account."""
        self.is_active = False
    
    def __str__(self) -> str:
        return f"{self.full_name} ({self.email})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, User):
            return False
        return self.user_id == other.user_id if self.user_id else False
    
    def __hash__(self) -> int:
        return hash(self.user_id) if self.user_id else hash(id(self))
