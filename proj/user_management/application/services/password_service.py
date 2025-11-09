"""
PasswordService: hashing, verification, strength validation, reset flow.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password

import jwt

from ...domain.exceptions import (
    WeakPasswordError,
    InvalidPasswordError,
    StudentCannotHavePasswordError,
    InvalidTokenError,
    ExpiredTokenError,
    InvalidTokenTypeError,
    TokenAlreadyUsedError,
    UserNotFoundError,
)
from ...infrastructure.repositories import UserRepository


PASSWORD_SPECIALS = r"!@#$%^&*()_+\-=\[\]{}|;:,.<>?"
SPECIALS_REGEX = re.escape(PASSWORD_SPECIALS)


@dataclass
class PasswordService:
    user_repository: UserRepository

    # Config
    reset_expiry_minutes: int = 60
    bcrypt_cost: int = 12  # informational; Django handles strength via hasher config

    def hash_password(self, plain_password: str) -> str:
        self.validate_password_strength(plain_password)
        return make_password(plain_password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        if not hashed_password:
            return False
        return check_password(plain_password, hashed_password)

    def validate_password_strength(self, password: str) -> None:
        if len(password) < 8:
            raise WeakPasswordError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", password):
            raise WeakPasswordError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise WeakPasswordError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", password):
            raise WeakPasswordError("Password must contain at least one digit")
        if not re.search(rf"[{SPECIALS_REGEX}]", password):
            raise WeakPasswordError("Password must contain at least one special character")

    def change_password(self, user_id: int, old_password: str, new_password: str) -> str:
        user = self.user_repository.get_by_id(user_id)
        if user.is_student():
            # Domain exception takes no arguments
            raise StudentCannotHavePasswordError()

        # We must fetch hashed password from ORM directly
        from ...infrastructure.orm.django_models import User as UserModel
        try:
            user_model = UserModel.objects.get(user_id=user_id)
        except UserModel.DoesNotExist:
            raise UserNotFoundError(f"User {user_id} not found")

        if not self.verify_password(old_password, user_model.password):
            raise InvalidPasswordError()

        if old_password == new_password:
            raise WeakPasswordError("New password must be different from old password")

        self.validate_password_strength(new_password)
        hashed = self.hash_password(new_password)
        self.user_repository.update_password(user_id, hashed)
        return "Password changed successfully"

    def generate_reset_token(self, user_id: int) -> str:
        # Ensure user exists and has password
        user = self.user_repository.get_by_id(user_id)
        if not (user.is_admin() or user.is_lecturer()):
            raise StudentCannotHavePasswordError()

        payload = {
            'user_id': user_id,
            'exp': datetime.now(tz=timezone.utc) + timedelta(minutes=self.reset_expiry_minutes),
            'iat': datetime.now(tz=timezone.utc),
            'type': 'password_reset',
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    def reset_password(self, reset_token: str, new_password: str) -> str:
        try:
            decoded = jwt.decode(reset_token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError as e:
            # Domain ExpiredTokenError takes no arguments
            raise ExpiredTokenError() from e
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError("Invalid reset token") from e

        if decoded.get('type') != 'password_reset':
            raise InvalidTokenTypeError('password_reset', decoded.get('type'))

        user_id = decoded.get('user_id')
        if not user_id:
            raise InvalidTokenError("Malformed reset token: missing user_id")

        # Optional: check token not used yet (requires persistence). Skipped for now.
        # If you later add a used-tokens store, raise TokenAlreadyUsedError when appropriate.

        self.validate_password_strength(new_password)
        hashed = self.hash_password(new_password)
        self.user_repository.update_password(user_id, hashed)
        return "Password reset successfully"
