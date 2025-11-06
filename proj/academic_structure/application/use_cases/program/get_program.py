"""Get Program use case."""

from typing import Optional

from ....domain.exceptions import ProgramNotFoundError
from ....infrastructure.repositories import ProgramRepository
from ...dto import ProgramDTO, to_program_dto


class GetProgramUseCase:
    """Use case for retrieving a single program by ID."""

    def __init__(self, program_repository: ProgramRepository):
        """Initialize use case with repository dependency.
        
        Args:
            program_repository: Repository for program data access
        """
        self.program_repository = program_repository

    def execute(self, program_id: int) -> ProgramDTO:
        """Get program by ID.
        
        Args:
            program_id: ID of the program to retrieve
            
        Returns:
            ProgramDTO with program data
            
        Raises:
            ProgramNotFoundError: If program with given ID does not exist
        """
        program = self.program_repository.find_by_id(program_id)
        
        if program is None:
            raise ProgramNotFoundError(f"Program with ID {program_id} not found")
        
        return to_program_dto(program)


class GetProgramByCodeUseCase:
    """Use case for retrieving a single program by code."""

    def __init__(self, program_repository: ProgramRepository):
        """Initialize use case with repository dependency.
        
        Args:
            program_repository: Repository for program data access
        """
        self.program_repository = program_repository

    def execute(self, program_code: str) -> ProgramDTO:
        """Get program by code (case-insensitive).
        
        Args:
            program_code: Code of the program to retrieve
            
        Returns:
            ProgramDTO with program data
            
        Raises:
            ProgramNotFoundError: If program with given code does not exist
        """
        program = self.program_repository.get_by_code(program_code)
        
        if program is None:
            raise ProgramNotFoundError(f"Program with code '{program_code}' not found")
        
        return to_program_dto(program)
