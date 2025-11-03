from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Program:
    """Domain entity representing an academic program.
    
    Immutable entity representing the state of a program.
    Business logic in domain services.
    """

    program_id: Optional[int]
    program_name: str
    program_code: str
    department_name: str
    has_streams: bool = False

    def __str__(self) -> str:
        return f"{self.program_code} - {self.program_name}"

    def requires_streams(self) -> bool:
        """Check if this program requires stream subdivisions."""
        return bool(self.has_streams)
