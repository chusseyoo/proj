"""Fixtures for Email Notifications interface API tests.

Self-contained so tests can run standalone within this folder.
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient
@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    from user_management.infrastructure.orm.django_models import User

    user = User.objects.create_user(
        email="admin@example.com",
        role=User.Roles.ADMIN,
        first_name="Admin",
        last_name="User",
        password="AdminPass123!",
        is_staff=True,
    )
    return user


@pytest.fixture
def lecturer_user(db):
    from user_management.infrastructure.orm.django_models import User

    user = User.objects.create_user(
        email="lecturer@example.com",
        role=User.Roles.LECTURER,
        first_name="John",
        last_name="Lecturer",
        password="LecturerPass123!",
    )
    return user



@pytest.fixture
def en_program(db):
    from academic_structure.infrastructure.orm.django_models import Program

    program, _ = Program.objects.get_or_create(
        program_code="BCS",
        defaults=dict(
            program_name="Bachelor of Computer Science",
            department_name="Computer Science",
            has_streams=True,
        ),
    )
    return program


@pytest.fixture
def en_stream(db, en_program):
    from academic_structure.infrastructure.orm.django_models import Stream

    return Stream.objects.create(
        program=en_program,
        stream_name="Main",
        year_of_study=2,
    )


@pytest.fixture
def en_lecturer_user_with_profile(db, lecturer_user):
    from user_management.infrastructure.orm.django_models import User, LecturerProfile

    # Ensure lecturer profile exists for the shared lecturer_user fixture
    from user_management.infrastructure.orm.django_models import LecturerProfile
    LecturerProfile.objects.get_or_create(user=lecturer_user, defaults={"department_name": "CS"})
    return lecturer_user


@pytest.fixture
def en_another_lecturer_with_profile(db):
    from user_management.infrastructure.orm.django_models import User, LecturerProfile

    user = User.objects.create_user(
        email="other.lecturer@example.com",
        role=User.Roles.LECTURER,
        first_name="Other",
        last_name="Lecturer",
        password="LecturerPass123!",
    )
    LecturerProfile.objects.create(user=user, department_name="CS")
    return user


@pytest.fixture
def en_course(db, en_program, en_lecturer_user_with_profile):
    from academic_structure.infrastructure.orm.django_models import Course
    from user_management.infrastructure.orm.django_models import LecturerProfile

    lecturer_profile = LecturerProfile.objects.get(user=en_lecturer_user_with_profile)
    return Course.objects.create(
        program=en_program,
        course_code="BCS101",
        course_name="Intro to CS",
        department_name="Computer Science",
        lecturer=lecturer_profile,
        is_active=True,
    )


@pytest.fixture
def en_session(db, en_program, en_course, en_lecturer_user_with_profile, en_stream):
    from session_management.infrastructure.orm.django_models import Session
    from user_management.infrastructure.orm.django_models import LecturerProfile

    lecturer_profile = LecturerProfile.objects.get(user=en_lecturer_user_with_profile)
    start = timezone.now()
    end = start + timedelta(hours=1)
    return Session.objects.create(
        program=en_program,
        course=en_course,
        lecturer=lecturer_profile,
        stream=en_stream,
        time_created=start,
        time_ended=end,
        latitude=0.12345678,
        longitude=36.12345678,
        location_description="Room 101",
    )


@pytest.fixture
def en_student_profiles(db, en_program, en_stream):
    from user_management.infrastructure.orm.django_models import User, StudentProfile

    students = []
    for i in range(1, 4):
        user = User.objects.create_user(
            email=f"student{i}@example.com",
            role=User.Roles.STUDENT,
            first_name="Stu",
            last_name=str(i),
            password=None,
        )
        sp = StudentProfile.objects.create(
            user=user,
            student_id=f"BCS/{100000+i}",
            program=en_program,
            stream=en_stream,
            year_of_study=2,
            qr_code_data=f"BCS/{100000+i}",
        )
        students.append(sp)
    return students


@pytest.fixture
def make_notifications(db):
    from email_notifications.models import EmailNotification
    from django.utils import timezone
    from datetime import timedelta

    def _maker(session, students, statuses):
        notifs = []
        now = timezone.now()
        for sp, status in zip(students, statuses):
            n = EmailNotification.objects.create(
                session=session,
                student_profile=sp,
                token=f"token-{sp.student_profile_id}",
                token_expires_at=now + timedelta(hours=1),
                status=status,
            )
            notifs.append(n)
        return notifs

    return _maker


@pytest.fixture
def authenticated_admin_client(admin_user):
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
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
    return client


@pytest.fixture
def authenticated_lecturer_client(lecturer_user):
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
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
    return client
