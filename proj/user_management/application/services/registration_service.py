"""
RegistrationService: registration flows for lecturer, student, admin.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from django.db import transaction

from ...domain.entities import User, UserRole
from ...domain.value_objects import Email, StudentId
from ...domain.exceptions import (
    EmailAlreadyExistsError,
    WeakPasswordError,
    UnauthorizedError,
    StudentIdAlreadyExistsError,
    InvalidStudentIdFormatError,
    StreamRequiredError,
    StreamNotAllowedError,
    StreamNotInProgramError,
)
from ...domain.services import IdentityService, EnrollmentService
from ...infrastructure.repositories import (
    UserRepository,
    StudentProfileRepository,
    LecturerProfileRepository,
)
from academic_structure.infrastructure.orm.django_models import Program as ProgramModel, Stream as StreamModel
from .password_service import PasswordService
from .authentication_service import AuthenticationService
from ...domain.entities import LecturerProfile as LP


@dataclass
class RegistrationService:
    user_repository: UserRepository
    student_repository: StudentProfileRepository
    lecturer_repository: LecturerProfileRepository
    password_service: PasswordService
    authentication_service: AuthenticationService

    @transaction.atomic
    def register_lecturer(self, lecturer_data: Dict) -> Dict:
        email = str(IdentityService.normalize_email(lecturer_data['email']))
        if self.user_repository.exists_by_email(email):
            raise EmailAlreadyExistsError('Email address is already registered')

        self.password_service.validate_password_strength(lecturer_data['password'])
        password_hash = self.password_service.hash_password(lecturer_data['password'])

        # Create user
        user = self.user_repository.create(
            User(
                user_id=None,
                first_name=lecturer_data['first_name'].strip(),
                last_name=lecturer_data['last_name'].strip(),
                email=Email(email),
                role=UserRole.LECTURER,
                is_active=True,
                has_password=True,
            ),
            password_hash=password_hash,
        )
        # Create profile
        profile = self.lecturer_repository.create(
            LP(
                lecturer_profile_id=None,
                user_id=user.user_id,
                department_name=lecturer_data['department_name'],
            )
        )

        # Login to return tokens
        tokens = self.authentication_service.login(email, lecturer_data['password'])
        return {'user': user, 'lecturer_profile': profile, **tokens}

    @transaction.atomic
    def register_student(self, student_data: Dict, admin_user: User) -> Dict:
        if not admin_user.is_admin():
            raise UnauthorizedError('Only administrators can register students')

        email = str(IdentityService.normalize_email(student_data['email']))
        if self.user_repository.exists_by_email(email):
            raise EmailAlreadyExistsError('Email address is already registered')

        student_id = StudentId(student_data['student_id'])
        if self.student_repository.exists_by_student_id(str(student_id)):
            raise StudentIdAlreadyExistsError('Student ID is already registered')

        # Program/Stream validations
        program = ProgramModel.objects.get(id=student_data['program_id'])
        program_has_streams = program.has_streams
        stream_id = student_data.get('stream_id')
        EnrollmentService.validate_stream_requirement(program_has_streams, stream_id)
        if stream_id is not None:
            try:
                stream = StreamModel.objects.get(id=stream_id)
            except StreamModel.DoesNotExist:
                raise StreamNotInProgramError('Stream does not belong to program')
            if stream.program_id != program.id:
                raise StreamNotInProgramError('Stream does not belong to program')

        EnrollmentService.validate_year_of_study(student_data['year_of_study'])

        # Create user (no password)
        user = self.user_repository.create(
            User(
                user_id=None,
                first_name=student_data['first_name'].strip(),
                last_name=student_data['last_name'].strip(),
                email=Email(email),
                role=UserRole.STUDENT,
                is_active=True,
                has_password=False,
            ),
            password_hash=None,
        )

        # Create profile
        from ...domain.entities import StudentProfile as SP
        profile = self.student_repository.create(
            SP(
                student_profile_id=None,
                student_id=student_id,
                user_id=user.user_id,
                program_id=program.id,
                stream_id=stream_id,
                year_of_study=student_data['year_of_study'],
                qr_code_data=str(student_id),
            )
        )

        return {'user': user, 'student_profile': profile}

    def register_admin(self, admin_data: Dict, creator_admin: User) -> Dict:
        if not creator_admin.is_admin():
            raise UnauthorizedError('Only administrators can create admins')

        email = str(IdentityService.normalize_email(admin_data['email']))
        if self.user_repository.exists_by_email(email):
            raise EmailAlreadyExistsError('Email address is already registered')

        self.password_service.validate_password_strength(admin_data['password'])
        password_hash = self.password_service.hash_password(admin_data['password'])

        user = self.user_repository.create(
            User(
                user_id=None,
                first_name=admin_data['first_name'].strip(),
                last_name=admin_data['last_name'].strip(),
                email=Email(email),
                role=UserRole.ADMIN,
                is_active=True,
                has_password=True,
            ),
            password_hash=password_hash,
        )

        return {'user': user}
