from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from ..services import AuthenticationService


@dataclass
class LoginUseCase:
    auth: AuthenticationService

    def handle(self, email: str, password: str) -> Dict:
        return self.auth.login(email, password)


@dataclass
class RefreshAccessTokenUseCase:
    auth: AuthenticationService

    def handle(self, refresh_token: str) -> Dict:
        # Returns {'access_token': str, 'refresh_token': Optional[str]}
        return self.auth.refresh_access_token(refresh_token)


@dataclass
class GenerateStudentAttendanceTokenUseCase:
    auth: AuthenticationService

    def handle(self, student_profile_id: int, session_id: int) -> Dict:
        token = self.auth.generate_student_attendance_token(student_profile_id, session_id)
        return {"attendance_token": token}
