import pytest

# Django DB tests required for infra layer
pytestmark = pytest.mark.django_db


# --- Academic Structure factories ---
@pytest.fixture
def program_factory():
    from academic_structure.infrastructure.orm.django_models import Program
    counter = {"value": 0}
    
    def _generate_code(index: int) -> str:
        """Generate unique 3-letter codes: AAA, AAB, ..., AAZ, ABA, ..., ZZZ"""
        letters = []
        num = index
        for _ in range(3):
            letters.append(chr(65 + (num % 26)))  # 65 = 'A'
            num //= 26
        return ''.join(reversed(letters))
    
    def _create_program(
        program_code: str | None = None,
        program_name: str | None = None,
        department_name: str = "Computer Science",
        has_streams: bool = True,
    ):
        if program_code is None:
            program_code = _generate_code(counter["value"])
        if program_name is None:
            program_name = f"Program {program_code}"
        counter["value"] += 1
        
        return Program.objects.create(
            program_code=program_code,
            program_name=program_name,
            department_name=department_name,
            has_streams=has_streams,
        )
    return _create_program


@pytest.fixture
def stream_factory(program_factory):
    from academic_structure.infrastructure.orm.django_models import Stream
    def _create_stream(
        program=None,
        stream_name: str = "Software Engineering",
        year_of_study: int = 2,
    ):
        program = program or program_factory()
        return Stream.objects.create(
            program=program,
            stream_name=stream_name,
            year_of_study=year_of_study,
        )
    return _create_stream


# --- User Management factories ---
@pytest.fixture
def user_factory():
    from user_management.infrastructure.orm.django_models import User as UserModel
    counter = {"value": 0}
    
    def _create_user(
        email: str | None = None,
        role: str = UserModel.Roles.LECTURER,
        first_name: str = "John",
        last_name: str = "Doe",
        password: str | None = "hashed_pw",
        is_active: bool = True,
    ):
        if email is None:
            email = f"user{counter['value']}@example.com"
        counter["value"] += 1
        
        # Note: UserModel.clean enforces password presence for Admin/Lecturer and absence for Student
        user = UserModel(
            email=email,
            role=role,
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user
    return _create_user


@pytest.fixture
def student_profile_factory(user_factory, program_factory):
    from user_management.infrastructure.orm.django_models import StudentProfile as StudentProfileModel
    def _create_student_profile(
        user=None,
        student_id: str = "BCS/123456",
        program=None,
        stream=None,
        year_of_study: int = 2,
        qr_code_data: str | None = None,
    ):
        user = user or user_factory(role="Student", password=None)
        program = program or program_factory()
        kwargs = {
            "user": user,
            "student_id": student_id,
            "program": program,
            "year_of_study": year_of_study,
        }
        if stream is not None:
            kwargs["stream"] = stream
        if qr_code_data is not None:
            kwargs["qr_code_data"] = qr_code_data
        profile = StudentProfileModel.objects.create(**kwargs)
        return profile
    return _create_student_profile


@pytest.fixture
def lecturer_profile_factory(user_factory):
    from user_management.infrastructure.orm.django_models import LecturerProfile as LecturerProfileModel
    def _create_lecturer_profile(
        user=None,
        department_name: str = "Computer Science",
    ):
        user = user or user_factory(role="Lecturer")
        profile = LecturerProfileModel.objects.create(
            user=user,
            department_name=department_name,
        )
        return profile
    return _create_lecturer_profile
