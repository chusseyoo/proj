"""Program domain service implementing business rules for programs."""

from ..entities.program import Program
from ..ports.program_repository import ProgramRepositoryPort
from ..exceptions import (
    ProgramNotFoundError,
    ProgramCodeAlreadyExistsError,
    ProgramCannotBeDeletedError,
    ValidationError,
)


class ProgramService:
    """Domain service for program-level business rules and validation."""

    def __init__(self, program_repo: ProgramRepositoryPort):
        self.program_repo = program_repo

    def can_be_deleted(self, program: Program) -> bool:
        """Check if a program can be safely deleted.
        
        A program can be deleted if there are no students and no courses.
        """
        if program.program_id is None:
            # not persisted — safe to remove conceptually
            return True

        students = self.program_repo.students_count(program.program_id)
        courses = self.program_repo.courses_count(program.program_id)
        return (students + courses) == 0

    def validate_program_code(self, code: str) -> str:
        """Validate and normalize program code.
        
        Returns uppercase code if valid, raises ValidationError otherwise.
        """
        if not code or not isinstance(code, str):
            raise ValidationError("Program code must be a non-empty string")
        
        normalized = code.strip().upper()
        
        if len(normalized) < 2 or len(normalized) > 6:
            raise ValidationError("Program code must be 2-6 characters")
        
        if not normalized.replace("_", "").isalnum():
            raise ValidationError("Program code must contain only letters, digits, and underscores")
        
        return normalized

    def validate_program_for_creation(self, data: dict) -> None:
        """Validate program data before creation."""
        # Validate code format
        code = data.get("program_code", "")
        normalized_code = self.validate_program_code(code)
        
        # Check uniqueness
        if self.program_repo.exists_by_code(normalized_code):
            raise ProgramCodeAlreadyExistsError(
                f"Program code '{normalized_code}' already exists"
            )
        
        # Validate name
        name = data.get("program_name", "")
        if not name or len(name) < 3:
            raise ValidationError("Program name must be at least 3 characters")
        
        if len(name) > 150:
            raise ValidationError("Program name must not exceed 150 characters")
        
        # Validate department
        dept = data.get("department_name", "")
        if not dept or len(dept) < 3:
            raise ValidationError("Department name must be at least 3 characters")

    def validate_program_for_deletion(self, program_id: int) -> None:
        """Validate program can be deleted, raise exception if not."""
        program = self.program_repo.get_by_id(program_id)
        if not self.can_be_deleted(program):
            raise ProgramCannotBeDeletedError(
                f"Cannot delete program {program.program_code}: has students or courses"
            )

