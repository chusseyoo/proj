"""
Repository for LecturerProfile entity.

Handles all data access operations for LecturerProfile model.
"""
from typing import Optional, List

from ..orm.django_models import LecturerProfile as LecturerProfileModel
from ...domain.entities import LecturerProfile
from ...domain.exceptions import LecturerNotFoundError


class LecturerProfileRepository:
    """
    Data access layer for LecturerProfile entity.
    """
    
    def get_by_id(self, lecturer_id: int) -> LecturerProfile:
        """
        Get by primary key.
        
        Args:
            lecturer_id: Lecturer profile's primary key
            
        Returns:
            LecturerProfile domain entity
            
        Raises:
            LecturerNotFoundError: If profile doesn't exist
        """
        try:
            profile_model = LecturerProfileModel.objects.get(
                lecturer_id=lecturer_id
            )
            return self._to_domain(profile_model)
        except LecturerProfileModel.DoesNotExist:
            raise LecturerNotFoundError(
                f"Lecturer profile with ID {lecturer_id} not found"
            )
    
    def get_by_user_id(self, user_id: int) -> LecturerProfile:
        """
        Get lecturer profile for a user.
        
        Args:
            user_id: User's ID
            
        Returns:
            LecturerProfile domain entity
            
        Raises:
            LecturerNotFoundError: If profile doesn't exist
        """
        try:
            profile_model = LecturerProfileModel.objects.get(user_id=user_id)
            return self._to_domain(profile_model)
        except LecturerProfileModel.DoesNotExist:
            raise LecturerNotFoundError(
                f"Lecturer profile for user {user_id} not found"
            )
    
    def find_by_user_id(self, user_id: int) -> Optional[LecturerProfile]:
        """
        Find by user_id, return None if not found.
        
        Args:
            user_id: User's ID
            
        Returns:
            LecturerProfile domain entity or None
        """
        try:
            return self.get_by_user_id(user_id)
        except LecturerNotFoundError:
            return None
    
    def exists_by_user_id(self, user_id: int) -> bool:
        """
        Check if lecturer profile exists for user.
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if profile exists
        """
        return LecturerProfileModel.objects.filter(user_id=user_id).exists()
    
    def list_by_department(self, department_name: str) -> List[LecturerProfile]:
        """
        Get all lecturers in a department.
        
        Args:
            department_name: Department name
            
        Returns:
            List of LecturerProfile domain entities
        """
        profile_models = LecturerProfileModel.objects.filter(
            department_name__iexact=department_name
        )
        return [self._to_domain(p) for p in profile_models]
    
    def list_all(self) -> List[LecturerProfile]:
        """
        Get all lecturer profiles.
        
        Returns:
            List of all LecturerProfile domain entities
        """
        profile_models = LecturerProfileModel.objects.all()
        return [self._to_domain(p) for p in profile_models]
    
    def create(self, profile: LecturerProfile) -> LecturerProfile:
        """
        Create lecturer profile.
        
        Args:
            profile: LecturerProfile domain entity
            
        Returns:
            Created LecturerProfile domain entity with ID assigned
        """
        profile_model = LecturerProfileModel(
            user_id=profile.user_id,
            department_name=profile.department_name,
        )
        profile_model.save()
        
        return self._to_domain(profile_model)
    
    def update(self, lecturer_id: int, **update_fields) -> LecturerProfile:
        """
        Update lecturer profile fields.
        
        Args:
            lecturer_id: Profile to update
            **update_fields: Fields to update
            
        Returns:
            Updated LecturerProfile domain entity
            
        Raises:
            LecturerNotFoundError: If profile doesn't exist
        """
        try:
            profile_model = LecturerProfileModel.objects.get(
                lecturer_id=lecturer_id
            )
            
            for field, value in update_fields.items():
                if hasattr(profile_model, field):
                    setattr(profile_model, field, value)
            
            profile_model.save()
            return self._to_domain(profile_model)
        except LecturerProfileModel.DoesNotExist:
            raise LecturerNotFoundError(
                f"Lecturer profile with ID {lecturer_id} not found"
            )
    
    def update_department(self, lecturer_id: int, department_name: str) -> LecturerProfile:
        """
        Update department only.
        
        Args:
            lecturer_id: Profile to update
            department_name: New department name
            
        Returns:
            Updated LecturerProfile domain entity
        """
        return self.update(lecturer_id, department_name=department_name)
    
    def delete(self, lecturer_id: int) -> None:
        """
        Delete lecturer profile.
        
        Args:
            lecturer_id: Profile to delete
            
        Raises:
            LecturerNotFoundError: If profile doesn't exist
        """
        try:
            profile_model = LecturerProfileModel.objects.get(
                lecturer_id=lecturer_id
            )
            profile_model.delete()
        except LecturerProfileModel.DoesNotExist:
            raise LecturerNotFoundError(
                f"Lecturer profile with ID {lecturer_id} not found"
            )
    
    def get_with_user(self, lecturer_id: int) -> LecturerProfile:
        """
        Get profile with user info (optimized).
        
        Args:
            lecturer_id: Profile ID
            
        Returns:
            LecturerProfile domain entity
            
        Raises:
            LecturerNotFoundError: If profile doesn't exist
        """
        try:
            profile_model = LecturerProfileModel.objects.select_related(
                'user'
            ).get(lecturer_id=lecturer_id)
            return self._to_domain(profile_model)
        except LecturerProfileModel.DoesNotExist:
            raise LecturerNotFoundError(
                f"Lecturer profile with ID {lecturer_id} not found"
            )
    
    def list_with_user_info(self) -> List[LecturerProfile]:
        """
        Get all lecturers with user info (optimized).
        
        Returns:
            List of LecturerProfile domain entities
        """
        profile_models = LecturerProfileModel.objects.select_related('user').all()
        return [self._to_domain(p) for p in profile_models]
    
    def _to_domain(self, profile_model: LecturerProfileModel) -> LecturerProfile:
        """
        Convert Django ORM model to domain entity.
        
        Args:
            profile_model: Django LecturerProfile model instance
            
        Returns:
            LecturerProfile domain entity
        """
        return LecturerProfile(
            lecturer_profile_id=profile_model.lecturer_id,
            user_id=profile_model.user_id,
            department_name=profile_model.department_name,
        )
