"""Update Program use case."""

from typing import Dict, Any

from ....domain.exceptions import ProgramNotFoundError, ValidationError
from ....infrastructure.repositories import ProgramRepository
from ...dto import ProgramDTO, to_program_dto


class UpdateProgramUseCase:
    """Use case for updating an existing program."""

    def __init__(self, program_repository: ProgramRepository):
        """Initialize use case with repository dependency.
        
        Args:
            program_repository: Repository for program data access
        """
        self.program_repository = program_repository

    def execute(self, program_id: int, updates: Dict[str, Any]) -> ProgramDTO:
        """Update an existing program.
        
        Only mutable fields can be updated: program_name, department_name, has_streams.
        program_code is immutable after creation (student IDs depend on it).
        
        Args:
            program_id: ID of the program to update
            updates: Dictionary with fields to update:
                - program_name (str, optional): New name (5-200 chars)
                - department_name (str, optional): New department
                - has_streams (bool, optional): New streams flag
                
        Returns:
            ProgramDTO with updated program data
            
        Raises:
            ProgramNotFoundError: If program does not exist
            ValidationError: If trying to update program_code or invalid data
        """
        # Check if program exists
        program = self.program_repository.get_by_id(program_id)
        if program is None:
            raise ProgramNotFoundError(f"Program with ID {program_id} not found")
        
        # Prevent program_code updates (immutable)
        if 'program_code' in updates:
            raise ValidationError(
                "program_code cannot be changed after creation (student IDs depend on it)"
            )
        
        # Validate updates
        allowed_fields = {'program_name', 'department_name', 'has_streams'}
        invalid_fields = set(updates.keys()) - allowed_fields
        if invalid_fields:
            raise ValidationError(
                f"Cannot update fields: {', '.join(invalid_fields)}"
            )
        
        # Validate program_name if provided
        if 'program_name' in updates:
            program_name = updates['program_name'].strip()
            if len(program_name) < 5 or len(program_name) > 200:
                raise ValidationError(
                    f"program_name must be between 5 and 200 characters, got: {len(program_name)}"
                )
            updates['program_name'] = program_name
        
        # Validate department_name if provided
        if 'department_name' in updates:
            department_name = updates['department_name'].strip()
            if len(department_name) < 3 or len(department_name) > 150:
                raise ValidationError(
                    f"department_name must be between 3 and 150 characters, got: {len(department_name)}"
                )
            updates['department_name'] = department_name
        
        # Update via repository
        updated_program = self.program_repository.update(program_id, updates)
        
        return to_program_dto(updated_program)
