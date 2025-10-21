"""
Email value object with validation following RFC 5322 standard.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    """
    Immutable value object representing a validated email address.
    
    Email addresses are stored in lowercase for case-insensitive comparison.
    """
    
    value: str
    
    def __post_init__(self):
        """Validate email format and normalize to lowercase."""
        if not self.value:
            raise ValueError("Email cannot be empty")
        
        # Normalize to lowercase
        normalized = self.value.lower().strip()
        object.__setattr__(self, 'value', normalized)
        
        # Validate format (simplified RFC 5322 pattern)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, normalized):
            raise ValueError(f"Invalid email format: {self.value}")
    
    def __str__(self) -> str:
        return self.value
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Email):
            return self.value == other.value
        return False
    
    def __hash__(self) -> int:
        return hash(self.value)
    
    @property
    def domain(self) -> str:
        """Extract domain part of email."""
        return self.value.split('@')[1] if '@' in self.value else ''
    
    @property
    def local_part(self) -> str:
        """Extract local part of email (before @)."""
        return self.value.split('@')[0] if '@' in self.value else self.value
