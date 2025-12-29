"""Pytest configuration for attendance_recording domain tests."""
import sys
from pathlib import Path
import pytest

# Add both roots to sys.path:
# - workspace root (contains manage.py)
# - inner package root (contains proj/__init__.py)
_here = Path(__file__).resolve()
WORKSPACE_ROOT = _here.parents[3]  # /home/.../proj
PACKAGE_ROOT = _here.parents[2]    # /home/.../proj/proj

for path in (str(WORKSPACE_ROOT), str(PACKAGE_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

print("[conftest] sys.path head:", sys.path[:5])

# Fail fast if package import breaks during test collection
import importlib
importlib.import_module("attendance_recording")


@pytest.fixture
def jwt_secret() -> str:
    """Secret key for JWT signing in tests."""
    return "test-secret-key"


def create_test_user(**kwargs):
    """Helper function to create test users with correct signature."""
    from user_management.models import User
    
    defaults = {
        'email': 'test@test.com',
        'role': 'Student',
        'first_name': 'Test',
        'last_name': 'User',
    }
    defaults.update(kwargs)
    
    return User.objects.create_user(**defaults)


def create_test_student_profile(user, student_id='BCS/234344', program=None, **kwargs):
    """Helper function to create test student profiles."""
    from user_management.models import StudentProfile
    
    # If no program provided, create one
    if program is None:
        from academic_structure.models import Program
        program, _ = Program.objects.get_or_create(
            program_code='BCS',
            defaults={
                'program_name': 'Bachelor of Computer Science',
                'department_name': 'Computer Science',
                'has_streams': False,
            }
        )
    
    defaults = {
        'user': user,
        'student_id': student_id,
        'program': program,
        'year_of_study': 2,
    }
    defaults.update(kwargs)
    
    return StudentProfile.objects.create(**defaults)


def create_test_session(lecturer_profile=None, program=None, course=None, **kwargs):
    """Helper function to create test sessions."""
    from decimal import Decimal
    from datetime import timedelta
    from django.utils import timezone
    from session_management.models import Session
    from user_management.models import LecturerProfile
    from academic_structure.models import Program, Course
    
    # If no lecturer provided, create one
    if lecturer_profile is None:
        lecturer_user = create_test_user(
            email=f'lecturer_{timezone.now().timestamp()}@test.com',
            role='Lecturer',
            first_name='Test',
            last_name='Lecturer',
            password='Passw0rd!'
        )
        lecturer_profile = LecturerProfile.objects.create(
            user=lecturer_user,
            department_name='Computer Science',
        )
    
    # If no program provided, create one
    if program is None:
        program, _ = Program.objects.get_or_create(
            program_code='BCS',
            defaults={
                'program_name': 'Bachelor of Computer Science',
                'department_name': 'Computer Science',
                'has_streams': False,
            }
        )
    
    # Handle course_id in kwargs (for backward compatibility)
    course_id = kwargs.pop('course_id', None)
    if course is None:
        if course_id is not None:
            # Create different courses based on course_id
            course_codes = {
                1: ('BCS012', 'Data Structures and Algorithms'),
                2: ('BCS023', 'Algorithms and Complexity'),
            }
            code, name = course_codes.get(course_id, ('BCS099', 'Test Course'))
            course, _ = Course.objects.get_or_create(
                course_code=code,
                defaults={
                    'program': program,
                    'course_name': name,
                    'department_name': 'Computer Science',
                }
            )
        else:
            # Default course
            course, _ = Course.objects.get_or_create(
                course_code='BCS012',
                defaults={
                    'program': program,
                    'course_name': 'Data Structures and Algorithms',
                    'department_name': 'Computer Science',
                }
            )
    
    defaults = {
        'program': program,
        'course': course,
        'lecturer': lecturer_profile,
        'time_created': timezone.now(),
        'time_ended': timezone.now() + timedelta(hours=2),
        'latitude': Decimal('-1.28333412'),
        'longitude': Decimal('36.81666588'),
    }
    defaults.update(kwargs)
    
    return Session.objects.create(**defaults)


# Infrastructure layer fixtures (Django ORM models)

@pytest.fixture
def sample_user(db):
    """Create a sample user for testing."""
    return create_test_user(
        email='testuser001@test.com',
        role='Student',
        first_name='Test',
        last_name='User',
    )


@pytest.fixture
def sample_student(db, sample_user):
    """Create a sample student profile for testing."""
    return create_test_student_profile(sample_user, student_id='BCS/234344')


@pytest.fixture
def sample_session(db):
    """Create a sample session for testing."""
    return create_test_session()
