from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Stream:
    """Domain entity representing a stream within a program.
    
    Streams are subdivisions of programs (e.g., Stream A, Evening cohort).
    Only exist when parent program has has_streams=True.
    """

    stream_id: Optional[int]
    stream_name: str
    program_id: int
    year_of_study: int

    def __str__(self) -> str:
        return f"Program({self.program_id}) Year {self.year_of_study} - {self.stream_name}"
