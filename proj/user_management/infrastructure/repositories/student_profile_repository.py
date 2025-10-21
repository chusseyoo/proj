"""
Repository for StudentProfile entity.

Handles all data access operations for StudentProfile model.
"""
from typing import Optional, List
from django.db import transaction

from ..orm.django_models import StudentProfile as StudentProfileModel
from ...domain.entities import StudentProfile
from ...domain.value_objects import StudentId
from ...domain.exceptions import (
    StudentNotFoundError,
    StudentIdAlreadyExistsError,
)


class StudentProfileRepository:
    """
    Data access layer for StudentProfile entity.
    """
    
    def get_by_id(self, student_profile_id: int) -> StudentProfile:
        """
        Get student profile by primary key.
        
        Args:
            student_profile_id: Student profile's primary key
            
        Returns:
            StudentProfile domain entity
            
        Raises:
            StudentNotFoundError: If profile doesn't exist
        """
        try:
            profile_model = StudentProfileModel.objects.get(
                student_profile_id=student_profile_id
            )
            return self._to_domain(profile_model)
        except StudentProfileModel.DoesNotExist:
            raise StudentNotFoundError(
                f"Student profile with ID {student_profile_id} not found"
            )
    
    def get_by_user_id(self, user_id: int) -> StudentProfile:
        """
        Get student profile for a user.
        
        Args:
            user_id: User's ID
            
        Returns:
            StudentProfile domain entity
            
        Raises:
            StudentNotFoundError: If profile doesn't exist
        """
        try:
            profile_model = StudentProfileModel.objects.get(user_id=user_id)
            return self._to_domain(profile_model)
        except StudentProfileModel.DoesNotExist:
            raise StudentNotFoundError(
                f"Student profile for user {user_id} not found"
            )
    
    def get_by_student_id(self, student_id: str) -> StudentProfile:
        """
        Get by institutional ID (e.g., BCS/234344).
        
        Args:
            student_id: Institutional student ID
            
        Returns:
            StudentProfile domain entity
            
        Raises:
            StudentNotFoundError: If profile doesn't exist
        """
        try:
            profile_model = StudentProfileModel.objects.get(
                student_id__iexact=student_id
            )
            return self._to_domain(profile_model)
        except StudentProfileModel.DoesNotExist:
            raise StudentNotFoundError(
                f"Student with ID {student_id} not found"
            )
    
    def find_by_user_id(self, user_id: int) -> Optional[StudentProfile]:
        """
        Find by user_id, return None if not found.
        
        Args:
            user_id: User's ID
            
        Returns:
            StudentProfile domain entity or None
        """
        try:
            return self.get_by_user_id(user_id)
        except StudentNotFoundError:
            return None
    
    def find_by_student_id(self, student_id: str) -> Optional[StudentProfile]:
        """
        Find by student_id, return None if not found.
        
        Args:
            student_id: Institutional student ID
            
        Returns:
            StudentProfile domain entity or None
        """
        try:
            return self.get_by_student_id(student_id)
        except StudentNotFoundError:
            return None
    
    def exists_by_student_id(self, student_id: str) -> bool:
        """
        Check if institutional student_id exists.
        
        Args:
            student_id: Student ID to check
            
        Returns:
            True if student_id exists
        """
        return StudentProfileModel.objects.filter(
            student_id__iexact=student_id
        ).exists()
    
    def exists_by_user_id(self, user_id: int) -> bool:
        """
        Check if student profile exists for user.
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if profile exists
        """
        return StudentProfileModel.objects.filter(user_id=user_id).exists()
    
    def list_by_program(self, program_id: int) -> List[StudentProfile]:
        """
        Get all students in a program.
        
        Args:
            program_id: Program ID
            
        Returns:
            List of StudentProfile domain entities
        """
        profile_models = StudentProfileModel.objects.filter(program_id=program_id)
        return [self._to_domain(p) for p in profile_models]
    
    def list_by_stream(self, stream_id: int) -> List[StudentProfile]:
        """
        Get all students in a stream.
        
        Args:
            stream_id: Stream ID
            
        Returns:
            List of StudentProfile domain entities
        """
        profile_models = StudentProfileModel.objects.filter(stream_id=stream_id)
        return [self._to_domain(p) for p in profile_models]
    
    def list_by_year(self, year_of_study: int) -> List[StudentProfile]:
        """
        Get all students in a specific year.
        
        Args:
            year_of_study: Year (1-4)
            
        Returns:
            List of StudentProfile domain entities
        """
        profile_models = StudentProfileModel.objects.filter(
            year_of_study=year_of_study
        )
        return [self._to_domain(p) for p in profile_models]
    
    def list_by_program_and_year(
        self, program_id: int, year_of_study: int
    ) -> List[StudentProfile]:
        """
        Get students in program and year.
        
        Args:
            program_id: Program ID
            year_of_study: Year (1-4)
            
        Returns:
            List of StudentProfile domain entities
        """
        profile_models = StudentProfileModel.objects.filter(
            program_id=program_id,
            year_of_study=year_of_study
        )
        return [self._to_domain(p) for p in profile_models]
    
    def create(self, profile: StudentProfile) -> StudentProfile:
        """
        Create student profile.
        
        Args:
            profile: StudentProfile domain entity
            
        Returns:
            Created StudentProfile domain entity with ID assigned
            
        Raises:
            StudentIdAlreadyExistsError: If student_id already exists
        """
        if self.exists_by_student_id(str(profile.student_id)):
            raise StudentIdAlreadyExistsError(
                f"Student ID {profile.student_id} already exists"
            )
        
        profile_model = StudentProfileModel(
            user_id=profile.user_id,
            student_id=str(profile.student_id),
            program_id=profile.program_id,
            stream_id=profile.stream_id,
            year_of_study=profile.year_of_study,
            qr_code_data=profile.qr_code_data,
        )
        profile_model.save()
        
        return self._to_domain(profile_model)
    
    def update(self, student_profile_id: int, **update_fields) -> StudentProfile:
        """
        Update student profile fields.
        
        Args:
            student_profile_id: Profile to update
            **update_fields: Fields to update
            
        Returns:
            Updated StudentProfile domain entity
            
        Raises:
            StudentNotFoundError: If profile doesn't exist
        """
        try:
            profile_model = StudentProfileModel.objects.get(
                student_profile_id=student_profile_id
            )
            
            for field, value in update_fields.items():
                if hasattr(profile_model, field):
                    setattr(profile_model, field, value)
            
            profile_model.save()
            return self._to_domain(profile_model)
        except StudentProfileModel.DoesNotExist:
            raise StudentNotFoundError(
                f"Student profile with ID {student_profile_id} not found"
            )
    
    def update_year(self, student_profile_id: int, year_of_study: int) -> StudentProfile:
        """
        Update year only.
        
        Args:
            student_profile_id: Profile to update
            year_of_study: New year (1-4)
            
        Returns:
            Updated StudentProfile domain entity
        """
        return self.update(student_profile_id, year_of_study=year_of_study)
    
    def update_stream(
        self, student_profile_id: int, stream_id: Optional[int]
    ) -> StudentProfile:
        """
        Update stream (can be NULL).
        
        Args:
            student_profile_id: Profile to update
            stream_id: New stream ID or None
            
        Returns:
            Updated StudentProfile domain entity
        """
        return self.update(student_profile_id, stream_id=stream_id)
    
    def delete(self, student_profile_id: int) -> None:
        """
        Delete student profile.
        
        Args:
            student_profile_id: Profile to delete
            
        Raises:
            StudentNotFoundError: If profile doesn't exist
        """
        try:
            profile_model = StudentProfileModel.objects.get(
                student_profile_id=student_profile_id
            )
            profile_model.delete()
        except StudentProfileModel.DoesNotExist:
            raise StudentNotFoundError(
                f"Student profile with ID {student_profile_id} not found"
            )
    
    def get_with_full_info(self, student_profile_id: int) -> StudentProfile:
        """
        Get profile with user, program, and stream (optimized).
        
        Args:
            student_profile_id: Profile ID
            
        Returns:
            StudentProfile domain entity
            
        Raises:
            StudentNotFoundError: If profile doesn't exist
        """
        try:
            profile_model = StudentProfileModel.objects.select_related(
                'user', 'program', 'stream'
            ).get(student_profile_id=student_profile_id)
            return self._to_domain(profile_model)
        except StudentProfileModel.DoesNotExist:
            raise StudentNotFoundError(
                f"Student profile with ID {student_profile_id} not found"
            )
    
    def _to_domain(self, profile_model: StudentProfileModel) -> StudentProfile:
        """
        Convert Django ORM model to domain entity.
        
        Args:
            profile_model: Django StudentProfile model instance
            
        Returns:
            StudentProfile domain entity
        """
        return StudentProfile(
            student_profile_id=profile_model.student_profile_id,
            student_id=StudentId(profile_model.student_id),
            user_id=profile_model.user_id,
            program_id=profile_model.program_id,
            stream_id=profile_model.stream_id,
            year_of_study=profile_model.year_of_study,
            qr_code_data=profile_model.qr_code_data,
        )
