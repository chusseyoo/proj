"""
Data Transfer Objects (DTOs) for User Management.

DTOs define the shape of data transferred between layers
(API ↔ Application ↔ Domain).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


# ============================================================================
# REQUEST DTOs (Input from API)
# ============================================================================

@dataclass
class RegisterLecturerRequestDTO:
    """DTO for lecturer self-registration."""
    first_name: str
    last_name: str
    email: str
    password: str
    department_name: str


@dataclass
class RegisterStudentRequestDTO:
    """DTO for student registration (admin only)."""
    student_id: str
    first_name: str
    last_name: str
    email: str
    program_id: int
    stream_id: Optional[int]
    year_of_study: int


@dataclass
class RegisterAdminRequestDTO:
    """DTO for admin registration (admin only)."""
    first_name: str
    last_name: str
    email: str
    password: str


@dataclass
class LoginRequestDTO:
    """DTO for user login."""
    email: str
    password: str


@dataclass
class UpdateUserRequestDTO:
    """DTO for updating user information."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None


@dataclass
class UpdateStudentProfileRequestDTO:
    """DTO for updating student profile."""
    year_of_study: Optional[int] = None
    stream_id: Optional[int] = None


@dataclass
class UpdateLecturerProfileRequestDTO:
    """DTO for updating lecturer profile."""
    department_name: Optional[str] = None


@dataclass
class ChangePasswordRequestDTO:
    """DTO for changing password."""
    old_password: str
    new_password: str


@dataclass
class ResetPasswordRequestDTO:
    """DTO for resetting password with token."""
    reset_token: str
    new_password: str


@dataclass
class GenerateResetTokenRequestDTO:
    """DTO for requesting password reset token."""
    email: str


# ============================================================================
# RESPONSE DTOs (Output to API)
# ============================================================================

@dataclass
class UserResponseDTO:
    """DTO for user details in API responses."""
    user_id: int
    first_name: str
    last_name: str
    email: str
    role: str
    is_active: bool
    date_joined: datetime
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass
class StudentProfileResponseDTO:
    """DTO for student profile in API responses."""
    student_profile_id: int
    student_id: str
    user_id: int
    program_id: int
    stream_id: Optional[int]
    year_of_study: int
    qr_code_data: str


@dataclass
class LecturerProfileResponseDTO:
    """DTO for lecturer profile in API responses."""
    lecturer_id: int
    user_id: int
    department_name: str


@dataclass
class LoginResponseDTO:
    """DTO for login response with tokens."""
    access_token: str
    refresh_token: str
    user: UserSummaryDTO


@dataclass
class UserSummaryDTO:
    """DTO for minimal user info (e.g., in login response)."""
    user_id: int
    email: str
    role: str
    full_name: str


@dataclass
class RegisterLecturerResponseDTO:
    """DTO for lecturer registration response."""
    user: UserResponseDTO
    lecturer_profile: LecturerProfileResponseDTO
    access_token: str
    refresh_token: str


@dataclass
class RegisterStudentResponseDTO:
    """DTO for student registration response."""
    user: UserResponseDTO
    student_profile: StudentProfileResponseDTO


@dataclass
class RegisterAdminResponseDTO:
    """DTO for admin registration response."""
    user: UserResponseDTO


@dataclass
class UserWithProfileResponseDTO:
    """DTO for user with their profile attached."""
    user: UserResponseDTO
    student_profile: Optional[StudentProfileResponseDTO] = None
    lecturer_profile: Optional[LecturerProfileResponseDTO] = None


@dataclass
class TokenResponseDTO:
    """DTO for token-only responses (refresh, attendance)."""
    token: str
    token_type: str
    expires_in: int  # seconds


@dataclass
class MessageResponseDTO:
    """DTO for simple message responses."""
    message: str
    status: str = "success"


@dataclass
class ErrorResponseDTO:
    """DTO for error responses."""
    error: str
    details: Optional[str] = None
    field_errors: Optional[dict] = None


# ============================================================================
# INTERNAL DTOs (Between Application Services)
# ============================================================================

@dataclass
class CreateUserDTO:
    """Internal DTO for creating user entity."""
    first_name: str
    last_name: str
    email: str
    role: str
    password_hash: Optional[str] = None


@dataclass
class CreateStudentProfileDTO:
    """Internal DTO for creating student profile."""
    user_id: int
    student_id: str
    program_id: int
    stream_id: Optional[int]
    year_of_study: int
    qr_code_data: str


@dataclass
class CreateLecturerProfileDTO:
    """Internal DTO for creating lecturer profile."""
    user_id: int
    department_name: str
