"""
UserService: user retrieval, updates, activation/deactivation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from ...domain.entities import User, UserRole
from ...domain.exceptions import (
    UserNotFoundError,
    EmailAlreadyExistsError,
    UnauthorizedError,
)
from ...domain.services import IdentityService
from ...infrastructure.repositories import (
    UserRepository,
    StudentProfileRepository,
    LecturerProfileRepository,
)


@dataclass
class UserService:
    user_repository: UserRepository
    student_repository: StudentProfileRepository
    lecturer_repository: LecturerProfileRepository

    def get_user_by_id(self, user_id: int, include_profile: bool = True) -> Dict:
        user = self.user_repository.get_by_id(user_id)
        return self._attach_profile(user) if include_profile else {'user': user}

    def get_user_by_email(self, email: str, include_profile: bool = True) -> Dict:
        user = self.user_repository.get_by_email(email.strip().lower())
        return self._attach_profile(user) if include_profile else {'user': user}

    def update_user(self, actor: User, user_id: int, update_data: Dict) -> User:
        # Email update: enforce uniqueness
        if 'email' in update_data and update_data['email']:
            email_norm = IdentityService.normalize_email(update_data['email'])
            if self.user_repository.exists_by_email(str(email_norm)):
                existing = self.user_repository.find_by_email(str(email_norm))
                if existing and existing.user_id != user_id:
                    raise EmailAlreadyExistsError("Email is already registered")
            update_data['email'] = str(email_norm)

        # These fields are safe to update directly; role change not allowed
        update_data.pop('role', None)
        return self.user_repository.update(user_id, **update_data)

    def activate_user(self, actor: User, user_id: int) -> User:
        self._ensure_admin(actor)
        return self.user_repository.activate(user_id)

    def deactivate_user(self, actor: User, user_id: int) -> User:
        self._ensure_admin(actor)
        # TODO: Cross-context call to deactivate lecturer sessions if needed
        return self.user_repository.deactivate(user_id)

    # Helpers
    def _ensure_admin(self, actor: User) -> None:
        if not actor.is_admin():
            raise UnauthorizedError("Only administrators can perform this action")

    def _attach_profile(self, user: User) -> Dict:
        payload: Dict[str, object] = {'user': user}
        if user.is_student():
            try:
                payload['student_profile'] = self.student_repository.get_by_user_id(user.user_id)
            except Exception:
                payload['student_profile'] = None
        elif user.is_lecturer():
            try:
                payload['lecturer_profile'] = self.lecturer_repository.get_by_user_id(user.user_id)
            except Exception:
                payload['lecturer_profile'] = None
        return payload
