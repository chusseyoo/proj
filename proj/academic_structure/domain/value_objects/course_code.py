import re
from dataclasses import dataclass
from typing import ClassVar

from ..exceptions import ValidationError


@dataclass(frozen=True)
class CourseCode:
    """Value object for course codes (2-4 uppercase letters + 3 digits)."""

    code: str
    PATTERN: ClassVar[re.Pattern] = re.compile(r"^[A-Z]{2,4}[0-9]{3}$")

    def __post_init__(self):
        value = (self.code or "").strip().upper()
        if not self.PATTERN.match(value):
            raise ValidationError(
                "Course code must be 2-4 uppercase letters followed by 3 digits (e.g., CS201)"
            )
        object.__setattr__(self, "code", value)
