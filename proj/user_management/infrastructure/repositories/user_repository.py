"""
Repository for User entity.

Handles all data access operations for User model,
translating between Django ORM and domain entities.
"""
from typing import Optional, List
from django.db.models import QuerySet

from ..orm.django_models import User as UserModel
from ...domain.entities import User, UserRole
from ...domain.value_objects import Email
from ...domain.exceptions import UserNotFoundError, EmailAlreadyExistsError


class UserRepository:
    """
    Data access layer for User entity.
    
    Translates between Django ORM models and domain entities.
    """
    
    def get_by_id(self, user_id: int) -> User:
        """
        Get user by primary key.
        
        Args:
            user_id: User's primary key
            
        Returns:
            User domain entity
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        try:
            user_model = UserModel.objects.get(user_id=user_id)
            return self._to_domain(user_model)
        except UserModel.DoesNotExist:
            raise UserNotFoundError(f"User with ID {user_id} not found")
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        """
        Find user by primary key, return None if not found.
        
        Args:
            user_id: User's primary key
            
        Returns:
            User domain entity or None
        """
        try:
            return self.get_by_id(user_id)
        except UserNotFoundError:
            return None
    
    def get_by_email(self, email: str) -> User:
        """
        Get user by email (case-insensitive).
        
        Args:
            email: User's email address
            
        Returns:
            User domain entity
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        try:
            user_model = UserModel.objects.get(email__iexact=email)
            return self._to_domain(user_model)
        except UserModel.DoesNotExist:
            raise UserNotFoundError(f"User with email {email} not found")
    
    def find_by_email(self, email: str) -> Optional[User]:
        """
        Find user by email, return None if not found.
        
        Args:
            email: User's email address
            
        Returns:
            User domain entity or None
        """
        try:
            return self.get_by_email(email)
        except UserNotFoundError:
            return None
    
    def exists_by_email(self, email: str) -> bool:
        """
        Check if email exists (case-insensitive).
        
        Args:
            email: Email to check
            
        Returns:
            True if email exists
        """
        return UserModel.objects.filter(email__iexact=email).exists()
    
    def exists_by_id(self, user_id: int) -> bool:
        """
        Check if user ID exists.
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if user exists
        """
        return UserModel.objects.filter(user_id=user_id).exists()
    
    def list_by_role(self, role: UserRole) -> List[User]:
        """
        Get all users with specific role.
        
        Args:
            role: UserRole enum value
            
        Returns:
            List of User domain entities
        """
        user_models = UserModel.objects.filter(role=role.value)
        return [self._to_domain(u) for u in user_models]
    
    def list_active(self) -> List[User]:
        """
        Get all active users.
        
        Returns:
            List of active User domain entities
        """
        user_models = UserModel.objects.filter(is_active=True)
        return [self._to_domain(u) for u in user_models]
    
    def list_active_by_role(self, role: UserRole) -> List[User]:
        """
        Get active users with specific role.
        
        Args:
            role: UserRole enum value
            
        Returns:
            List of active User domain entities
        """
        user_models = UserModel.objects.filter(role=role.value, is_active=True)
        return [self._to_domain(u) for u in user_models]
    
    def create(self, user: User, password_hash: Optional[str] = None) -> User:
        """
        Create new user.
        
        Args:
            user: User domain entity
            password_hash: Hashed password (None for students)
            
        Returns:
            Created User domain entity with ID assigned
            
        Raises:
            EmailAlreadyExistsError: If email already registered
        """
        if self.exists_by_email(str(user.email)):
            raise EmailAlreadyExistsError(f"Email {user.email} already exists")
        
        user_model = UserModel(
            first_name=user.first_name,
            last_name=user.last_name,
            email=str(user.email),
            role=user.role.value,
            is_active=user.is_active,
        )
        
        # Set password based on role
        if password_hash:
            user_model.password = password_hash
        else:
            user_model.set_unusable_password()
        
        user_model.save()
        
        return self._to_domain(user_model)
    
    def update(self, user_id: int, **update_fields) -> User:
        """
        Update user fields.
        
        Args:
            user_id: User to update
            **update_fields: Fields to update
            
        Returns:
            Updated User domain entity
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        try:
            user_model = UserModel.objects.get(user_id=user_id)
            
            # Update allowed fields
            for field, value in update_fields.items():
                if hasattr(user_model, field):
                    setattr(user_model, field, value)
            
            user_model.save()
            return self._to_domain(user_model)
        except UserModel.DoesNotExist:
            raise UserNotFoundError(f"User with ID {user_id} not found")
    
    def activate(self, user_id: int) -> User:
        """
        Set is_active=True.
        
        Args:
            user_id: User to activate
            
        Returns:
            Updated User domain entity
        """
        return self.update(user_id, is_active=True)
    
    def deactivate(self, user_id: int) -> User:
        """
        Set is_active=False (soft delete).
        
        Args:
            user_id: User to deactivate
            
        Returns:
            Updated User domain entity
        """
        return self.update(user_id, is_active=False)
    
    def update_password(self, user_id: int, password_hash: str) -> User:
        """
        Update password field only.
        
        Args:
            user_id: User to update
            password_hash: New hashed password
            
        Returns:
            Updated User domain entity
        """
        return self.update(user_id, password=password_hash)
    
    def delete(self, user_id: int) -> None:
        """
        Hard delete user (cascades to profiles).
        
        Args:
            user_id: User to delete
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        try:
            user_model = UserModel.objects.get(user_id=user_id)
            user_model.delete()
        except UserModel.DoesNotExist:
            raise UserNotFoundError(f"User with ID {user_id} not found")
    
    def _to_domain(self, user_model: UserModel) -> User:
        """
        Convert Django ORM model to domain entity.
        
        Args:
            user_model: Django User model instance
            
        Returns:
            User domain entity
        """
        return User(
            user_id=user_model.user_id,
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            email=Email(user_model.email),
            role=UserRole(user_model.role),
            is_active=user_model.is_active,
            has_password=user_model.has_usable_password(),
            date_joined=user_model.date_joined,
        )
