"""
ChangePasswordService: verify old password and update to new password.
"""
from __future__ import annotations

from dataclasses import dataclass

from ...domain.exceptions import (
    InvalidPasswordError,
    WeakPasswordError,
    UserNotFoundError,
    StudentCannotHavePasswordError,
)
from ...infrastructure.repositories import UserRepository
from .password_service import PasswordService


@dataclass
class ChangePasswordService:
    user_repository: UserRepository
    password_service: PasswordService

    def change_password(self, user_id: int, old_password: str, new_password: str) -> None:
        """
        Change user's password after verifying the old password.

        Rules:
        - Students cannot have passwords (raise StudentCannotHavePasswordError)
        - Old password must be correct (InvalidPasswordError if not)
        - New password must meet strength requirements (WeakPasswordError)
        """
        # Fetch user entity and ORM model for password hash
        user = self.user_repository.get_by_id(user_id)

        if user.is_student():
            raise StudentCannotHavePasswordError()

        # Obtain current password hash from ORM
        from ...infrastructure.orm.django_models import User as UserModel
        try:
            user_model = UserModel.objects.get(user_id=user.user_id)
        except UserModel.DoesNotExist as e:
            raise UserNotFoundError(str(user_id)) from e

        # Verify old password
        if not self.password_service.verify_password(old_password, user_model.password or ""):
            raise InvalidPasswordError()

        # Validate and set new password
        self.password_service.validate_password_strength(new_password)
        new_hash = self.password_service.hash_password(new_password)
        self.user_repository.update_password(user.user_id, new_hash)
