from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from ..services import RegistrationService
from ...domain.entities import User


@dataclass
class RegisterLecturerUseCase:
    registration: RegistrationService

    def handle(self, lecturer_data: Dict) -> Dict:
        return self.registration.register_lecturer(lecturer_data)


@dataclass
class RegisterStudentUseCase:
    registration: RegistrationService

    def handle(self, student_data: Dict, admin_user: User) -> Dict:
        return self.registration.register_student(student_data, admin_user)


@dataclass
class RegisterAdminUseCase:
    registration: RegistrationService

    def handle(self, admin_data: Dict, creator_admin: User) -> Dict:
        return self.registration.register_admin(admin_data, creator_admin)
