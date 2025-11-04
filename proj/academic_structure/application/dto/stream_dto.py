"""Stream Data Transfer Object and mapper."""

from dataclasses import dataclass
from typing import Optional

from ...domain.entities.stream import Stream


@dataclass
class StreamDTO:
    """Data Transfer Object for Stream entity.
    
    Used to transfer stream data between application layer and API/UI.
    Optionally includes program_code for enrichment.
    """
    stream_id: Optional[int]
    stream_name: str
    program_id: int
    year_of_study: int
    program_code: Optional[str] = None  # Optional enrichment from related Program


def to_stream_dto(stream: Stream, program_code: Optional[str] = None) -> StreamDTO:
    """Convert Stream domain entity to StreamDTO.
    
    Args:
        stream: Stream domain entity
        program_code: Optional program code for enrichment (can be fetched if needed)
        
    Returns:
        StreamDTO with data from domain entity
    """
    return StreamDTO(
        stream_id=stream.stream_id,
        stream_name=stream.stream_name,
        program_id=stream.program_id,
        year_of_study=stream.year_of_study,
        program_code=program_code,
    )
