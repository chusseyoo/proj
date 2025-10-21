"""
Domain service for identity-related operations.

Domain services encapsulate business logic that doesn't naturally fit
within a single entity. IdentityService handles cross-entity identity logic.
"""
from typing import Optional

from ..entities import User, UserRole
from ..value_objects import Email
from ..exceptions import (
    EmailAlreadyExistsError,
    StudentCannotHavePasswordError,
)


class IdentityService:
    """
    Domain service for identity-related business logic.
    
    Responsibilities:
    - Validate unique identities (email uniqueness logic)
    - Enforce password rules based on role
    - Coordinate identity constraints across entities
    """
    
    @staticmethod
    def validate_password_requirement(role: UserRole, has_password: bool) -> None:
        """
        Enforce business rule: Students cannot have passwords,
        Admin and Lecturer must have passwords.
        
        Args:
            role: User's role
            has_password: Whether password is set
            
        Raises:
            StudentCannotHavePasswordError: If student has password
            ValueError: If non-student lacks password
        """
        if role == UserRole.STUDENT and has_password:
            raise StudentCannotHavePasswordError(
                "Students use passwordless authentication"
            )
        
        if role in (UserRole.ADMIN, UserRole.LECTURER) and not has_password:
            raise ValueError(
                f"{role.value} users must have a password"
            )
    
    @staticmethod
    def can_user_login_with_password(user: User) -> bool:
        """
        Determine if user can authenticate with password.
        
        Business rule: Only Admin and Lecturer can use password login.
        Students use passwordless authentication (email links).
        
        Args:
            user: User entity
            
        Returns:
            True if user can login with password
        """
        return user.has_password and not user.is_student()
    
    @staticmethod
    def normalize_email(email: str) -> Email:
        """
        Normalize email for consistent storage and comparison.
        
        Args:
            email: Raw email string
            
        Returns:
            Email value object (normalized to lowercase)
        """
        return Email(email.lower().strip())
