"""Delete Program use case."""

from ....domain.exceptions import ProgramNotFoundError, ProgramCannotBeDeletedError
from ....infrastructure.repositories import ProgramRepository


class DeleteProgramUseCase:
    """Use case for safely deleting a program."""

    def __init__(self, program_repository: ProgramRepository):
        """Initialize use case with repository dependency.
        
        Args:
            program_repository: Repository for program data access
        """
        self.program_repository = program_repository

    def execute(self, program_id: int) -> None:
        """Delete a program if it has no dependencies.
        
        A program can only be deleted if:
        - It has no enrolled students
        - It has no courses
        - Streams will cascade delete automatically
        
        Args:
            program_id: ID of the program to delete
            
        Raises:
            ProgramNotFoundError: If program does not exist
            ProgramCannotBeDeletedError: If program has students or courses
        """
        # Check if program exists
        program = self.program_repository.get_by_id(program_id)
        if program is None:
            raise ProgramNotFoundError(f"Program with ID {program_id} not found")
        
        # Check if program can be deleted (no students, no courses)
        if not self.program_repository.can_be_deleted(program_id):
            # Get counts for error message
            students_count = self.program_repository.students_count(program_id)
            courses_count = self.program_repository.courses_count(program_id)
            
            reasons = []
            if students_count > 0:
                reasons.append(f"{students_count} enrolled student(s)")
            if courses_count > 0:
                reasons.append(f"{courses_count} course(s)")
            
            raise ProgramCannotBeDeletedError(
                f"Cannot delete program '{program.program_code}': "
                f"has {', '.join(reasons)}"
            )
        
        # Delete program (streams will cascade)
        self.program_repository.delete(program_id)
