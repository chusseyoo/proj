"""
AuthenticationService: login, JWT generation/validation, refresh, attendance token.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from uuid import uuid4

from django.conf import settings
import jwt

from ...domain.exceptions import (
    InvalidCredentialsError,
    StudentCannotLoginError,
    UserInactiveError,
    InvalidTokenError,
    ExpiredTokenError,
    InvalidTokenTypeError,
    UserNotFoundError,
)
from ...domain.entities import User
from ...infrastructure.repositories import UserRepository, StudentProfileRepository
from ..ports import RefreshTokenStorePort, RefreshTokenRecord
from .password_service import PasswordService


@dataclass
class AuthenticationService:
    user_repository: UserRepository
    password_service: PasswordService
    student_repository: StudentProfileRepository
    refresh_store: Optional[RefreshTokenStorePort] = None

    access_minutes: int = 15
    refresh_days: int = 7
    attendance_hours: int = 2

    def login(self, email: str, password: str) -> Dict:
        email_norm = email.strip().lower()
        user = self.user_repository.find_by_email(email_norm)
        if not user:
            raise InvalidCredentialsError()

        # Fetch hashed password from ORM
        from ...infrastructure.orm.django_models import User as UserModel
        try:
            user_model = UserModel.objects.get(user_id=user.user_id)
        except UserModel.DoesNotExist:
            raise InvalidCredentialsError()

        if user.is_student():
            raise StudentCannotLoginError()

        if not self.password_service.verify_password(password, user_model.password):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise UserInactiveError()

        access = self.generate_access_token(user)
        refresh = self.generate_refresh_token(user)
        return {
            'access_token': access,
            'refresh_token': refresh,
            'user': {
                'user_id': user.user_id,
                'email': str(user.email),
                'role': user.role.value,
                'full_name': user.full_name,
            }
        }

    def generate_access_token(self, user: User) -> str:
        payload = {
            'user_id': user.user_id,
            'email': str(user.email),
            'role': user.role.value,
            'exp': datetime.now(tz=timezone.utc) + timedelta(minutes=self.access_minutes),
            'iat': datetime.now(tz=timezone.utc),
            'type': 'access',
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    def generate_refresh_token(self, user: User) -> str:
        now = datetime.now(tz=timezone.utc)
        exp = now + timedelta(days=self.refresh_days)
        jti = uuid4().hex
        payload = {
            'jti': jti,
            'user_id': user.user_id,
            'exp': exp,
            'iat': now,
            'type': 'refresh',
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        if self.refresh_store:
            record = RefreshTokenRecord(jti=jti, user_id=user.user_id, issued_at=now, expires_at=exp)
            try:
                self.refresh_store.save(record)
            except Exception:
                # Non-fatal: allow stateless fallback
                pass
        return token

    def validate_token(self, token: str, token_type: str = 'access') -> Dict:
        try:
            decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError as e:
            raise ExpiredTokenError() from e
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError("Invalid token") from e

        # Enforce presence of expiration for all first-party tokens
        if 'exp' not in decoded:
            raise InvalidTokenError("Missing exp")

        if decoded.get('type') != token_type:
            raise InvalidTokenTypeError(token_type, decoded.get('type'))

        return decoded

    def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Validate the refresh token and return a new access token.
        If a refresh token store is configured, rotate the refresh token and return a new one.
        Returns dict: {'access_token': str, 'refresh_token': Optional[str]}
        """
        decoded = self.validate_token(refresh_token, token_type='refresh')
        jti = decoded.get('jti')
        user_id = decoded.get('user_id')
        if not user_id:
            raise InvalidTokenError("Malformed refresh token")

        # If we have a store, enforce revocation/rotation
        if self.refresh_store and jti:
            try:
                is_revoked = self.refresh_store.is_revoked(jti)
            except Exception:
                # If store check fails, fall back to stateless mode
                is_revoked = False
            
            if is_revoked:
                raise InvalidTokenError("Refresh token has been revoked")

        user = self.user_repository.get_by_id(user_id)
        if not user.is_active:
            raise UserInactiveError()

        access = self.generate_access_token(user)

        new_refresh = None
        if self.refresh_store and jti:
            # Rotate: revoke old and issue new
            now = datetime.now(tz=timezone.utc)
            exp = now + timedelta(days=self.refresh_days)
            new_jti = uuid4().hex
            payload = {
                'jti': new_jti,
                'user_id': user.user_id,
                'exp': exp,
                'iat': now,
                'type': 'refresh',
            }
            new_refresh = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
            record = RefreshTokenRecord(jti=new_jti, user_id=user.user_id, issued_at=now, expires_at=exp)
            try:
                self.refresh_store.rotate(jti, record)
            except Exception:
                # If rotation fails, do not return new refresh; access is still valid
                new_refresh = None

        return {'access_token': access, 'refresh_token': new_refresh}

    def revoke_refresh_token(self, refresh_token: str) -> None:
        """Revoke the provided refresh token via the store, if configured."""
        if not self.refresh_store:
            return
        try:
            decoded = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
            if decoded.get('type') != 'refresh':
                raise InvalidTokenTypeError('refresh', decoded.get('type'))
            jti = decoded.get('jti')
            if jti:
                self.refresh_store.revoke(jti)
        except jwt.ExpiredSignatureError:
            # Expired tokens can be considered already invalid; nothing to revoke
            pass
        except jwt.InvalidTokenError:
            # Ignore invalid tokens for revoke
            pass

    def generate_student_attendance_token(self, student_profile_id: int, session_id: int) -> str:
        # Validate student exists
        self.student_repository.get_by_id(student_profile_id)
        payload = {
            'student_profile_id': student_profile_id,
            'session_id': session_id,
            'exp': datetime.now(tz=timezone.utc) + timedelta(hours=self.attendance_hours),
            'iat': datetime.now(tz=timezone.utc),
            'type': 'attendance',
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
