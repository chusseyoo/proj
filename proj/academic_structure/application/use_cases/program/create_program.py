"""Create Program use case."""

from typing import Dict, Any

from ....domain.exceptions import ProgramCodeAlreadyExistsError, ValidationError
from ....infrastructure.repositories import ProgramRepository
from ...dto import ProgramDTO, to_program_dto


class CreateProgramUseCase:
    """Use case for creating a new program."""

    def __init__(self, program_repository: ProgramRepository):
        """Initialize use case with repository dependency.
        
        Args:
            program_repository: Repository for program data access
        """
        self.program_repository = program_repository

    def execute(self, data: Dict[str, Any]) -> ProgramDTO:
        """Create a new program.
        
        Args:
            data: Dictionary with program data:
                - program_name (str): Name of the program (5-200 chars)
                - program_code (str): 3-letter uppercase code
                - department_name (str): Department offering the program
                - has_streams (bool): Whether program has streams
                
        Returns:
            ProgramDTO with created program data
            
        Raises:
            ValidationError: If input data is invalid
            ProgramCodeAlreadyExistsError: If program_code already exists
        """
        # Validate required fields
        required_fields = ['program_name', 'program_code', 'department_name']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Extract and normalize data
        program_code = data['program_code'].upper().strip()
        program_name = data['program_name'].strip()
        department_name = data['department_name'].strip()
        has_streams = data.get('has_streams', False)
        
        # Validate program_code format (3 uppercase letters)
        if not program_code.isalpha() or len(program_code) != 3:
            raise ValidationError(
                f"program_code must be exactly 3 uppercase letters, got: '{program_code}'"
            )
        
        # Validate program_name length
        if len(program_name) < 5 or len(program_name) > 200:
            raise ValidationError(
                f"program_name must be between 5 and 200 characters, got: {len(program_name)}"
            )
        
        # Validate department_name length
        if len(department_name) < 5 or len(department_name) > 50:
            raise ValidationError(
                f"department_name must be between 5 and 50 characters, got: {len(department_name)}"
            )
        
        # Check uniqueness
        if self.program_repository.exists_by_code(program_code):
            raise ProgramCodeAlreadyExistsError(
                f"Program with code '{program_code}' already exists"
            )
        
        # Create program via repository
        program_data = {
            'program_name': program_name,
            'program_code': program_code,
            'department_name': department_name,
            'has_streams': has_streams,
        }
        
        program = self.program_repository.create(program_data)
        
        return to_program_dto(program)
