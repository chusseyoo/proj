"""
Port for refresh token storage, rotation, and revocation.

Application services depend on this interface; provide an infrastructure
implementation (e.g., DB table, cache, Redis) later.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class RefreshTokenRecord:
    jti: str
    user_id: int
    issued_at: datetime
    expires_at: datetime
    revoked_at: Optional[datetime] = None


class RefreshTokenStorePort(ABC):
    """Abstract port for persisting and validating refresh tokens."""

    @abstractmethod
    def save(self, record: RefreshTokenRecord) -> None:
        """Persist a new refresh token record."""

    @abstractmethod
    def get(self, jti: str) -> Optional[RefreshTokenRecord]:
        """Retrieve a stored refresh token by its JTI."""

    @abstractmethod
    def revoke(self, jti: str, when: Optional[datetime] = None) -> None:
        """Mark a refresh token as revoked."""

    @abstractmethod
    def is_revoked(self, jti: str) -> bool:
        """Check if a refresh token has been revoked."""

    @abstractmethod
    def rotate(self, old_jti: str, new_record: RefreshTokenRecord) -> None:
        """
        Atomically revoke the old token and persist the new one.
        Implementations should ensure this is safe under concurrency.
        """
