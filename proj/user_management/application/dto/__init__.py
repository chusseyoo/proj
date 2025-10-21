"""
Data Transfer Objects and Mappers for User Management.
"""

from .user_dtos import (
    # Request DTOs
    RegisterLecturerRequestDTO,
    RegisterStudentRequestDTO,
    RegisterAdminRequestDTO,
    LoginRequestDTO,
    UpdateUserRequestDTO,
    UpdateStudentProfileRequestDTO,
    UpdateLecturerProfileRequestDTO,
    ChangePasswordRequestDTO,
    ResetPasswordRequestDTO,
    GenerateResetTokenRequestDTO,
    
    # Response DTOs
    UserResponseDTO,
    StudentProfileResponseDTO,
    LecturerProfileResponseDTO,
    LoginResponseDTO,
    UserSummaryDTO,
    RegisterLecturerResponseDTO,
    RegisterStudentResponseDTO,
    RegisterAdminResponseDTO,
    UserWithProfileResponseDTO,
    TokenResponseDTO,
    MessageResponseDTO,
    ErrorResponseDTO,
    
    # Internal DTOs
    CreateUserDTO,
    CreateStudentProfileDTO,
    CreateLecturerProfileDTO,
)

from .mappers import (
    UserMapper,
    StudentProfileMapper,
    LecturerProfileMapper,
    RegistrationMapper,
    ProfileMapper,
)

__all__ = [
    # Request DTOs
    'RegisterLecturerRequestDTO',
    'RegisterStudentRequestDTO',
    'RegisterAdminRequestDTO',
    'LoginRequestDTO',
    'UpdateUserRequestDTO',
    'UpdateStudentProfileRequestDTO',
    'UpdateLecturerProfileRequestDTO',
    'ChangePasswordRequestDTO',
    'ResetPasswordRequestDTO',
    'GenerateResetTokenRequestDTO',
    
    # Response DTOs
    'UserResponseDTO',
    'StudentProfileResponseDTO',
    'LecturerProfileResponseDTO',
    'LoginResponseDTO',
    'UserSummaryDTO',
    'RegisterLecturerResponseDTO',
    'RegisterStudentResponseDTO',
    'RegisterAdminResponseDTO',
    'UserWithProfileResponseDTO',
    'TokenResponseDTO',
    'MessageResponseDTO',
    'ErrorResponseDTO',
    
    # Internal DTOs
    'CreateUserDTO',
    'CreateStudentProfileDTO',
    'CreateLecturerProfileDTO',
    
    # Mappers
    'UserMapper',
    'StudentProfileMapper',
    'LecturerProfileMapper',
    'RegistrationMapper',
    'ProfileMapper',
]
