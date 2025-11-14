"""
DRF Serializers for User Management API.

Handles request/response validation for authentication, registration,
user management, and profile management endpoints.
"""
from rest_framework import serializers


# ============================================================================
# AUTH SERIALIZERS
# ============================================================================

class LoginSerializer(serializers.Serializer):
    """Login request validation."""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})


class LoginResponseSerializer(serializers.Serializer):
    """Login response format."""
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user = serializers.DictField()


class RefreshTokenSerializer(serializers.Serializer):
    """Refresh token request validation."""
    refresh_token = serializers.CharField(required=True, write_only=True)


class RefreshTokenResponseSerializer(serializers.Serializer):
    """Refresh token response format."""
    access_token = serializers.CharField()
    refresh_token = serializers.CharField(required=False, allow_null=True)


# ============================================================================
# REGISTRATION SERIALIZERS
# ============================================================================

class RegisterLecturerSerializer(serializers.Serializer):
    """Lecturer self-registration request validation."""
    first_name = serializers.CharField(required=True, max_length=50, min_length=2)
    last_name = serializers.CharField(required=True, max_length=50, min_length=2)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    department_name = serializers.CharField(required=True, max_length=100, min_length=3)


class RegisterStudentSerializer(serializers.Serializer):
    """Student registration request validation (admin-only)."""
    student_id = serializers.RegexField(
        regex=r'^[A-Z]{3}/[0-9]{6}$',  # Uppercase letters only
        required=True,
        error_messages={'invalid': 'Student ID must follow format: ABC/123456 (uppercase letters only)'}
    )
    first_name = serializers.CharField(required=True, max_length=50, min_length=2)
    last_name = serializers.CharField(required=True, max_length=50, min_length=2)
    email = serializers.EmailField(required=True)
    program_id = serializers.IntegerField(required=True, min_value=1)
    stream_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    year_of_study = serializers.IntegerField(required=True, min_value=1, max_value=4)
    
    def validate_student_id(self, value):
        """Ensure student_id is uppercase and trimmed."""
        return value.strip() if value else value


class RegisterAdminSerializer(serializers.Serializer):
    """Admin registration request validation (admin-only)."""
    first_name = serializers.CharField(required=True, max_length=50, min_length=2)
    last_name = serializers.CharField(required=True, max_length=50, min_length=2)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )


class RegistrationResponseSerializer(serializers.Serializer):
    """Registration success response."""
    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    role = serializers.CharField()
    is_active = serializers.BooleanField()
    # For lecturer registration, also includes tokens
    access_token = serializers.CharField(required=False)
    refresh_token = serializers.CharField(required=False)
    # For student registration
    student_profile_id = serializers.IntegerField(required=False)
    student_id = serializers.CharField(required=False)


# ============================================================================
# USER SERIALIZERS
# ============================================================================

class UserSerializer(serializers.Serializer):
    """User detail response."""
    user_id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField()
    is_active = serializers.BooleanField()
    date_joined = serializers.DateTimeField()


class UpdateUserSerializer(serializers.Serializer):
    """User update request (partial)."""
    first_name = serializers.CharField(required=False, max_length=50, min_length=2)
    last_name = serializers.CharField(required=False, max_length=50, min_length=2)
    email = serializers.EmailField(required=False)


# ============================================================================
# PROFILE SERIALIZERS
# ============================================================================

class StudentProfileSerializer(serializers.Serializer):
    """Student profile response."""
    student_profile_id = serializers.IntegerField()
    student_id = serializers.CharField()
    user_id = serializers.IntegerField()
    program_id = serializers.IntegerField()
    stream_id = serializers.IntegerField(allow_null=True)
    year_of_study = serializers.IntegerField()
    qr_code_data = serializers.CharField()


class UpdateStudentProfileSerializer(serializers.Serializer):
    """Student profile update request (partial)."""
    year_of_study = serializers.IntegerField(required=False, min_value=1, max_value=4)
    stream_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)


class LecturerProfileSerializer(serializers.Serializer):
    """Lecturer profile response."""
    lecturer_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    department_name = serializers.CharField()


class UpdateLecturerProfileSerializer(serializers.Serializer):
    """Lecturer profile update request (partial)."""
    department_name = serializers.CharField(required=False, max_length=100, min_length=3)
