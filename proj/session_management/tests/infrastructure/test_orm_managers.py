from datetime import timedelta

import pytest
from django.utils import timezone

from session_management.infrastructure.orm.django_models import Session
from academic_structure.infrastructure.orm.django_models import Program, Course
from user_management.infrastructure.orm.django_models import User, LecturerProfile


@pytest.fixture
def test_data():
    """Create minimal FK objects for tests."""
    # Create Program
    program = Program.objects.create(
        program_name="Bachelor of Computer Science",
        program_code="BCS",
        department_name="Computing",
        has_streams=False,
    )
    
    # Create User for Lecturer
    user = User.objects.create_user(
        email="test.lecturer@example.com",
        role=User.Roles.LECTURER,
        first_name="Test",
        last_name="Lecturer",
        password="testpass123",
    )
    
    # Create LecturerProfile
    lecturer = LecturerProfile.objects.create(
        user=user,
        department_name="Computing",
    )
    
    # Create Course
    course = Course.objects.create(
        program=program,
        course_code="BCS012",
        course_name="Data Structures",
        department_name="Computing",
        lecturer=lecturer,
    )
    
    return {
        "program": program,
        "course": course,
        "lecturer": lecturer,
    }


@pytest.mark.django_db
def test_active_manager(test_data):
    now = timezone.now()
    s = Session.objects.create(
        program_id=test_data["program"].program_id,
        course_id=test_data["course"].course_id,
        lecturer_id=test_data["lecturer"].lecturer_id,
        stream_id=None,
        date_created=now.date(),
        time_created=now - timedelta(minutes=10),
        time_ended=now + timedelta(minutes=10),
        latitude=0.0,
        longitude=0.0,
    )

    qs = Session.objects.active(now)
    assert qs.filter(session_id=s.session_id).exists()


@pytest.mark.django_db
def test_overlapping_manager(test_data):
    start = timezone.now()
    s = Session.objects.create(
        program_id=test_data["program"].program_id,
        course_id=test_data["course"].course_id,
        lecturer_id=test_data["lecturer"].lecturer_id,
        stream_id=None,
        date_created=start.date(),
        time_created=start,
        time_ended=start + timedelta(hours=1),
        latitude=0.0,
        longitude=0.0,
    )

    # overlapping window (starts inside existing session)
    exists = Session.objects.overlapping_exists(
        test_data["lecturer"].lecturer_id,
        start + timedelta(minutes=30),
        start + timedelta(hours=2)
    )
    assert exists is True
