from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from ..services import UserService
from ...domain.entities import User


@dataclass
class GetUserByIdUseCase:
    users: UserService

    def handle(self, user_id: int, include_profile: bool = True) -> Dict:
        return self.users.get_user_by_id(user_id, include_profile=include_profile)


@dataclass
class GetUserByEmailUseCase:
    users: UserService

    def handle(self, email: str, include_profile: bool = True) -> Dict:
        return self.users.get_user_by_email(email, include_profile=include_profile)


@dataclass
class UpdateUserUseCase:
    users: UserService

    def handle(self, actor: User, user_id: int, update_data: Dict) -> User:
        return self.users.update_user(actor, user_id, update_data)


@dataclass
class ActivateUserUseCase:
    users: UserService

    def handle(self, actor: User, user_id: int) -> User:
        return self.users.activate_user(actor, user_id)


@dataclass
class DeactivateUserUseCase:
    users: UserService

    def handle(self, actor: User, user_id: int) -> User:
        return self.users.deactivate_user(actor, user_id)
