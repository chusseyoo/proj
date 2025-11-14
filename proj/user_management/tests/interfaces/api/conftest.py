import pytest

from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def program(db):
    # import lazily to avoid app loading issues in test discovery
    from academic_structure.infrastructure.orm.django_models import Program
    program_values = dict(
        program_name="Bachelor of Computer Science",
        program_code="BCS",
        department_name="Computer Science",
        has_streams=True,
    )

    program, created = Program.objects.get_or_create(program_code=program_values["program_code"], defaults=program_values)
    # Ensure fields are up-to-date in case an existing fixture has different attributes
    if not created:
        for k, v in program_values.items():
            setattr(program, k, v)
        program.save()

    return program


@pytest.fixture
def stream(db, program):
    from academic_structure.infrastructure.orm.django_models import Stream

    stream = Stream.objects.create(
        program=program,
        stream_name="Main",
        year_of_study=2,
    )
    return stream


@pytest.fixture
def admin_user(db):
    from user_management.infrastructure.orm.django_models import User

    return User.objects.create_user(
        email="admin@example.com",
        role=User.Roles.ADMIN,
        first_name="Admin",
        last_name="Creator",
        password="AdminPass123!",
    )


@pytest.fixture
def lecturer_user(db):
    from user_management.infrastructure.orm.django_models import User

    return User.objects.create_user(
        email="lecturer@example.com",
        role=User.Roles.LECTURER,
        first_name="Lec",
        last_name="Turer",
        password="LecturerPass123!",
    )


@pytest.fixture
def student_user(db, program, stream):
    from user_management.infrastructure.orm.django_models import User, StudentProfile

    user = User.objects.create_user(
        email="student@example.com",
        role=User.Roles.STUDENT,
        first_name="Stu",
        last_name="Dent",
        password=None,
    )

    StudentProfile.objects.create(
        user=user,
        student_id="BCS/000001",
        program=program,
        stream=stream,
        year_of_study=2,
    )

    return user
"""
Shared fixtures for API tests.

Provides authenticated API clients and sample data.
"""
import pytest
from rest_framework.test import APIClient
from django.contrib.auth.hashers import make_password

from user_management.infrastructure.orm.django_models import (
    User as UserModel,
    StudentProfile as StudentProfileModel,
    LecturerProfile as LecturerProfileModel,
)
from academic_structure.infrastructure.orm.django_models import Program, Stream


@pytest.fixture
def api_client():
    """Unauthenticated API client."""
    return APIClient()


@pytest.fixture
def sample_program(db):
    """Create a sample program for testing."""
    return Program.objects.create(
        program_code="BCS",
        program_name="Bachelor of Computer Science",
        department_name="Computer Science",
        has_streams=True,
    )


@pytest.fixture
def sample_program_no_streams(db):
    """Create a program without streams."""
    return Program.objects.create(
        program_code="BBA",
        program_name="Bachelor of Business Administration",
        department_name="Business",
        has_streams=False,
    )


@pytest.fixture
def sample_stream(db, sample_program):
    """Create a sample stream."""
    return Stream.objects.create(
        program=sample_program,
        stream_name="Software Engineering",
        year_of_study=2,
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    user = UserModel.objects.create(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        role=UserModel.Roles.ADMIN,
        is_active=True,
        is_staff=True,
    )
    user.set_password("AdminPass123!")
    user.save()
    return user


@pytest.fixture
def lecturer_user(db):
    """Create a lecturer user with profile."""
    user = UserModel.objects.create(
        email="lecturer@example.com",
        first_name="John",
        last_name="Lecturer",
        role=UserModel.Roles.LECTURER,
        is_active=True,
    )
    user.set_password("LecturerPass123!")
    user.save()
    
    LecturerProfileModel.objects.create(
        user=user,
        department_name="Computer Science",
    )
    return user


@pytest.fixture
def student_user(db, sample_program):
    """Create a student user with profile."""
    user = UserModel.objects.create(
        email="student@example.com",
        first_name="Jane",
        last_name="Student",
        role=UserModel.Roles.STUDENT,
        is_active=True,
    )
    user.set_unusable_password()
    user.save()
    
    StudentProfileModel.objects.create(
        user=user,
        student_id="BCS/123456",
        program=sample_program,
        year_of_study=2,
        qr_code_data="BCS/123456",
    )
    return user


@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    """API client authenticated as admin."""
    from user_management.application.services.authentication_service import AuthenticationService
    from user_management.application.services.password_service import PasswordService
    from user_management.infrastructure.repositories.user_repository import UserRepository
    from user_management.infrastructure.repositories.student_profile_repository import StudentProfileRepository
    
    user_repo = UserRepository()
    password_service = PasswordService(user_repository=user_repo)
    student_repo = StudentProfileRepository()
    
    auth_service = AuthenticationService(
        user_repository=user_repo,
        password_service=password_service,
        student_repository=student_repo,
    )
    
    tokens = auth_service.login(email="admin@example.com", password="AdminPass123!")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
    return api_client


@pytest.fixture
def authenticated_lecturer_client(api_client, lecturer_user):
    """API client authenticated as lecturer."""
    from user_management.application.services.authentication_service import AuthenticationService
    from user_management.application.services.password_service import PasswordService
    from user_management.infrastructure.repositories.user_repository import UserRepository
    from user_management.infrastructure.repositories.student_profile_repository import StudentProfileRepository
    
    user_repo = UserRepository()
    password_service = PasswordService(user_repository=user_repo)
    student_repo = StudentProfileRepository()
    
    auth_service = AuthenticationService(
        user_repository=user_repo,
        password_service=password_service,
        student_repository=student_repo,
    )
    
    tokens = auth_service.login(email="lecturer@example.com", password="LecturerPass123!")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
    return api_client


@pytest.fixture
def authenticated_student_client(api_client, student_user):
    """API client with student attendance token (for attendance marking)."""
    from user_management.application.services.authentication_service import AuthenticationService
    from user_management.application.services.password_service import PasswordService
    from user_management.infrastructure.repositories.user_repository import UserRepository
    from user_management.infrastructure.repositories.student_profile_repository import StudentProfileRepository
    
    user_repo = UserRepository()
    password_service = PasswordService(user_repository=user_repo)
    student_repo = StudentProfileRepository()
    
    auth_service = AuthenticationService(
        user_repository=user_repo,
        password_service=password_service,
        student_repository=student_repo,
    )
    
    # Generate attendance token for student
    profile = student_repo.get_by_user_id(student_user.user_id)
    
    token = auth_service.generate_student_attendance_token(
        student_profile_id=profile.student_profile_id,
        session_id=1,  # Dummy session ID
    )
    
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client

