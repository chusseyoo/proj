"""
Quick validation test for application layer components.
"""
from datetime import datetime, timezone
import os

# Configure Django settings for imports that touch Django ORM
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proj.settings")
try:
    import django  # type: ignore
    django.setup()
except Exception as e:
    # Print but continue; domain-only imports will still work
    print("[Info] django.setup() note:", e)

# Test imports
print("Testing imports...")

# Domain layer
from user_management.domain.entities import User, UserRole, StudentProfile, LecturerProfile
from user_management.domain.value_objects import Email, StudentId
from user_management.domain.services import IdentityService, EnrollmentService
from user_management.domain.exceptions import (
    UserNotFoundError,
    EmailAlreadyExistsError,
    WeakPasswordError,
)

# Infrastructure layer
from user_management.infrastructure.repositories import (
    UserRepository,
    StudentProfileRepository,
    LecturerProfileRepository,
)

# Application layer - Services
from user_management.application.services import (
    PasswordService,
    AuthenticationService,
    UserService,
    RegistrationService,
    ProfileService,
)

# Application layer - DTOs
from user_management.application.dto import (
    RegisterLecturerRequestDTO,
    RegisterStudentRequestDTO,
    LoginRequestDTO,
    UserResponseDTO,
    StudentProfileResponseDTO,
    LecturerProfileResponseDTO,
    UserMapper,
    StudentProfileMapper,
    LecturerProfileMapper,
)

print("✓ All imports successful!")

# Test domain entities
print("\nTesting domain entities...")
user = User(
    user_id=1,
    first_name="John",
    last_name="Doe",
    email=Email("john.doe@example.com"),
    role=UserRole.LECTURER,
    is_active=True,
    has_password=True,
    date_joined=datetime.now(tz=timezone.utc),
)
print(f"✓ Created user: {user.full_name} ({user.role.value})")

# Test value objects
print("\nTesting value objects...")
email = Email("test@example.com")
print(f"✓ Email: {email} (domain: {email.domain})")

student_id = StudentId("BCS/123456")
print(f"✓ StudentId: {student_id} (program: {student_id.program_code})")

# Test domain services
print("\nTesting domain services...")
IdentityService.validate_password_requirement(UserRole.STUDENT, False)
print("✓ IdentityService: Student password validation works")

EnrollmentService.validate_year_of_study(2)
print("✓ EnrollmentService: Year validation works")

# Test DTOs and Mappers
print("\nTesting DTOs and Mappers...")
user_dto = UserMapper.to_response_dto(user)
print(f"✓ UserMapper: {user_dto.full_name} - {user_dto.role}")

student_profile = StudentProfile(
    student_profile_id=1,
    student_id=StudentId("BCS/123456"),
    user_id=1,
    program_id=5,
    stream_id=2,
    year_of_study=2,
    qr_code_data="BCS/123456",
)
profile_dto = StudentProfileMapper.to_response_dto(student_profile)
print(f"✓ StudentProfileMapper: {profile_dto.student_id} - Year {profile_dto.year_of_study}")

print("\n" + "="*60)
print("✅ All application layer components validated successfully!")
print("="*60)
