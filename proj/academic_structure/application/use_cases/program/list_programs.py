"""List Programs use case."""

from typing import List, Optional

from ....infrastructure.repositories import ProgramRepository
from ...dto import ProgramDTO, to_program_dto


class ListProgramsUseCase:
    """Use case for listing programs with optional filtering."""

    def __init__(self, program_repository: ProgramRepository):
        """Initialize use case with repository dependency.
        
        Args:
            program_repository: Repository for program data access
        """
        self.program_repository = program_repository

    def execute(
        self,
        department_name: Optional[str] = None,
        has_streams: Optional[bool] = None
    ) -> List[ProgramDTO]:
        """List programs with optional filters.
        
        Args:
            department_name: Optional filter by department name
            has_streams: Optional filter by has_streams flag
            
        Returns:
            List of ProgramDTOs
        """
        if department_name and has_streams is not None:
            # Both filters applied
            programs = self.program_repository.list_by_department(department_name)
            programs = [p for p in programs if p.has_streams == has_streams]
        elif department_name:
            # Department filter only
            programs = self.program_repository.list_by_department(department_name)
        elif has_streams is not None:
            # Streams filter only
            if has_streams:
                programs = self.program_repository.list_with_streams()
            else:
                programs = self.program_repository.list_without_streams()
        else:
            # No filters
            programs = self.program_repository.list_all()
        
        return [to_program_dto(program) for program in programs]
