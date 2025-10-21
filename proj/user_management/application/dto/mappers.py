"""
DTO Mappers for User Management.

Converts between domain entities and DTOs.
"""
from __future__ import annotations

from typing import Dict, Optional

from ...domain.entities import User, StudentProfile, LecturerProfile
from .user_dtos import (
    UserResponseDTO,
    StudentProfileResponseDTO,
    LecturerProfileResponseDTO,
    UserSummaryDTO,
    UserWithProfileResponseDTO,
    LoginResponseDTO,
    RegisterLecturerResponseDTO,
    RegisterStudentResponseDTO,
    RegisterAdminResponseDTO,
)


class UserMapper:
    """Maps User domain entity to DTOs."""
    
    @staticmethod
    def to_response_dto(user: User) -> UserResponseDTO:
        """Convert User entity to UserResponseDTO."""
        return UserResponseDTO(
            user_id=user.user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=str(user.email),
            role=user.role.value,
            is_active=user.is_active,
            date_joined=user.date_joined,
        )
    
    @staticmethod
    def to_summary_dto(user: User) -> UserSummaryDTO:
        """Convert User entity to UserSummaryDTO (minimal info)."""
        return UserSummaryDTO(
            user_id=user.user_id,
            email=str(user.email),
            role=user.role.value,
            full_name=user.full_name,
        )
    
    @staticmethod
    def to_login_response(
        user: User,
        access_token: str,
        refresh_token: str
    ) -> LoginResponseDTO:
        """Convert login result to LoginResponseDTO."""
        return LoginResponseDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserMapper.to_summary_dto(user),
        )


class StudentProfileMapper:
    """Maps StudentProfile domain entity to DTOs."""
    
    @staticmethod
    def to_response_dto(profile: StudentProfile) -> StudentProfileResponseDTO:
        """Convert StudentProfile entity to DTO."""
        return StudentProfileResponseDTO(
            student_profile_id=profile.student_profile_id,
            student_id=str(profile.student_id),
            user_id=profile.user_id,
            program_id=profile.program_id,
            stream_id=profile.stream_id,
            year_of_study=profile.year_of_study,
            qr_code_data=profile.qr_code_data,
        )


class LecturerProfileMapper:
    """Maps LecturerProfile domain entity to DTOs."""
    
    @staticmethod
    def to_response_dto(profile: LecturerProfile) -> LecturerProfileResponseDTO:
        """Convert LecturerProfile entity to DTO."""
        return LecturerProfileResponseDTO(
            lecturer_id=profile.lecturer_profile_id,
            user_id=profile.user_id,
            department_name=profile.department_name,
        )


class RegistrationMapper:
    """Maps registration results to DTOs."""
    
    @staticmethod
    def to_lecturer_response(
        user: User,
        lecturer_profile: LecturerProfile,
        access_token: str,
        refresh_token: str
    ) -> RegisterLecturerResponseDTO:
        """Convert lecturer registration result to DTO."""
        return RegisterLecturerResponseDTO(
            user=UserMapper.to_response_dto(user),
            lecturer_profile=LecturerProfileMapper.to_response_dto(lecturer_profile),
            access_token=access_token,
            refresh_token=refresh_token,
        )
    
    @staticmethod
    def to_student_response(
        user: User,
        student_profile: StudentProfile
    ) -> RegisterStudentResponseDTO:
        """Convert student registration result to DTO."""
        return RegisterStudentResponseDTO(
            user=UserMapper.to_response_dto(user),
            student_profile=StudentProfileMapper.to_response_dto(student_profile),
        )
    
    @staticmethod
    def to_admin_response(user: User) -> RegisterAdminResponseDTO:
        """Convert admin registration result to DTO."""
        return RegisterAdminResponseDTO(
            user=UserMapper.to_response_dto(user),
        )


class ProfileMapper:
    """Maps user with profile to DTOs."""
    
    @staticmethod
    def to_user_with_profile(
        user: User,
        student_profile: Optional[StudentProfile] = None,
        lecturer_profile: Optional[LecturerProfile] = None
    ) -> UserWithProfileResponseDTO:
        """Convert user with profile to DTO."""
        return UserWithProfileResponseDTO(
            user=UserMapper.to_response_dto(user),
            student_profile=(
                StudentProfileMapper.to_response_dto(student_profile)
                if student_profile else None
            ),
            lecturer_profile=(
                LecturerProfileMapper.to_response_dto(lecturer_profile)
                if lecturer_profile else None
            ),
        )
    
    @staticmethod
    def from_service_result(result: Dict) -> UserWithProfileResponseDTO:
        """Convert service result dict to DTO."""
        user = result['user']
        student_profile = result.get('student_profile')
        lecturer_profile = result.get('lecturer_profile')
        
        return ProfileMapper.to_user_with_profile(
            user=user,
            student_profile=student_profile,
            lecturer_profile=lecturer_profile,
        )
