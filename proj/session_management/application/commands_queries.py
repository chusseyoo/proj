"""Commands and Queries definitions for the application layer.

Lightweight dataclasses used by application use-cases and builders. These
represent the expected shapes for commands/queries passed from an API layer
or test harness into the application.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class CreateSessionCommand:
    program_id: int
    course_id: int
    time_created: datetime
    time_ended: datetime
    latitude: str
    longitude: str
    location_description: Optional[str] = None
    stream_id: Optional[int] = None


@dataclass(frozen=True)
class ListSessionsQuery:
    page: int = 1
    page_size: int = 20
    program_id: Optional[int] = None
    course_id: Optional[int] = None
    stream_id: Optional[int] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None


@dataclass(frozen=True)
class GetSessionQuery:
    session_id: int


@dataclass(frozen=True)
class EndSessionCommand:
    session_id: int
    now: Optional[datetime] = None


@dataclass(frozen=True)
class UpdateSessionCommand:
    session_id: int
    time_created: Optional[datetime] = None
    time_ended: Optional[datetime] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    location_description: Optional[str] = None
    stream_id: Optional[int] = None

