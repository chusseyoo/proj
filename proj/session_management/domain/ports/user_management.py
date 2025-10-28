from __future__ import annotations

from typing import Protocol


class UserManagementPort(Protocol):
    """Port to query user/lecturer information."""

    def is_lecturer_active(self, lecturer_id: int) -> bool:
        ...
