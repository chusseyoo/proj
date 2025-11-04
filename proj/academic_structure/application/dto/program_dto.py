"""Program Data Transfer Object and mapper."""

from dataclasses import dataclass
from typing import Optional

from ...domain.entities.program import Program


@dataclass
class ProgramDTO:
    """Data Transfer Object for Program entity.
    
    Used to transfer program data between application layer and API/UI.
    """
    program_id: Optional[int]
    program_name: str
    program_code: str
    department_name: str
    has_streams: bool


def to_program_dto(program: Program) -> ProgramDTO:
    """Convert Program domain entity to ProgramDTO.
    
    Args:
        program: Program domain entity
        
    Returns:
        ProgramDTO with data from domain entity
    """
    return ProgramDTO(
        program_id=program.program_id,
        program_name=program.program_name,
        program_code=program.program_code,
        department_name=program.department_name,
        has_streams=program.has_streams,
    )
