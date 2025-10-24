"""Report entity/aggregate scaffold.

Minimal dataclass representing a persisted report record. In the real
implementation this may map to a Django model; the dataclass here is for
in-memory representations used by the application layer.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Report:
    id: Optional[int]
    session_id: int
    generated_by: int
    generated_date: Optional[str]
    file_path: Optional[str] = None
    file_type: Optional[str] = None
