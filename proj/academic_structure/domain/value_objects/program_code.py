import re
from dataclasses import dataclass
from typing import ClassVar

from ..exceptions import ValidationError


@dataclass(frozen=True)
class ProgramCode:
    """Value object for program codes (exactly 3 uppercase letters)."""

    code: str
    PATTERN: ClassVar[re.Pattern] = re.compile(r"^[A-Z]{3}$")

    def __post_init__(self):
        value = (self.code or "").strip().upper()
        if not self.PATTERN.match(value):
            raise ValidationError(
                "Program code must be exactly 3 uppercase letters (e.g., BCS, ENG)"
            )
        object.__setattr__(self, "code", value)
