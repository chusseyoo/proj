from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from ..services import ProfileService


@dataclass
class GetStudentProfileUseCase:
    profiles: ProfileService

    def handle(self, student_profile_id: int) -> Dict:
        return self.profiles.get_student_profile(student_profile_id)


@dataclass
class GetStudentProfileByUserIdUseCase:
    profiles: ProfileService

    def handle(self, user_id: int) -> Dict:
        return self.profiles.get_student_profile_by_user_id(user_id)


@dataclass
class GetStudentProfileByStudentIdUseCase:
    profiles: ProfileService

    def handle(self, student_id: str) -> Dict:
        return self.profiles.get_student_profile_by_student_id(student_id)


@dataclass
class UpdateStudentProfileUseCase:
    profiles: ProfileService

    def handle(self, student_profile_id: int, update_data: Dict) -> Dict:
        return self.profiles.update_student_profile(student_profile_id, update_data)


@dataclass
class GetLecturerProfileUseCase:
    profiles: ProfileService

    def handle(self, lecturer_id: int) -> Dict:
        return self.profiles.get_lecturer_profile(lecturer_id)


@dataclass
class GetLecturerProfileByUserIdUseCase:
    profiles: ProfileService

    def handle(self, user_id: int) -> Dict:
        return self.profiles.get_lecturer_profile_by_user_id(user_id)


@dataclass
class UpdateLecturerProfileUseCase:
    profiles: ProfileService

    def handle(self, lecturer_id: int, update_data: Dict) -> Dict:
        return self.profiles.update_lecturer_profile(lecturer_id, update_data)
