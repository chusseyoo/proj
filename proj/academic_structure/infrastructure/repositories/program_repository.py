"""Program repository implementation using Django ORM."""

from typing import Optional, Iterable

from ...domain.entities.program import Program as DomainProgram
from ...domain.ports.program_repository import ProgramRepositoryPort
from ..orm.django_models import Program as ORMProgram


class ProgramRepository:
    """ORM-backed implementation of ProgramRepositoryPort."""

    def _to_domain(self, orm_program: ORMProgram) -> DomainProgram:
        """Convert ORM model to domain entity."""
        return DomainProgram(
            program_id=orm_program.program_id,
            program_name=orm_program.program_name,
            program_code=orm_program.program_code,
            department_name=orm_program.department_name,
            has_streams=orm_program.has_streams,
        )

    def _to_orm_data(self, domain_program: DomainProgram) -> dict:
        """Convert domain entity to ORM data dict."""
        data = {
            "program_name": domain_program.program_name,
            "program_code": domain_program.program_code,
            "department_name": domain_program.department_name,
            "has_streams": domain_program.has_streams,
        }
        if domain_program.program_id is not None:
            data["program_id"] = domain_program.program_id
        return data

    def get_by_id(self, program_id: int) -> DomainProgram:
        """Get program by ID. Raises Program.DoesNotExist if not found."""
        orm_program = ORMProgram.objects.get(program_id=program_id)
        return self._to_domain(orm_program)

    def find_by_id(self, program_id: int) -> Optional[DomainProgram]:
        """Get program by ID, return None if not found."""
        try:
            return self.get_by_id(program_id)
        except ORMProgram.DoesNotExist:
            return None

    def get_by_code(self, program_code: str) -> DomainProgram:
        """Get program by code (case-insensitive). Raises if not found."""
        orm_program = ORMProgram.objects.get(program_code__iexact=program_code)
        return self._to_domain(orm_program)

    def exists_by_code(self, program_code: str) -> bool:
        """Check if program code already exists."""
        return ORMProgram.objects.filter(program_code__iexact=program_code).exists()

    def exists_by_id(self, program_id: int) -> bool:
        """Check if program exists by ID."""
        return ORMProgram.objects.filter(program_id=program_id).exists()

    def list_all(self) -> Iterable[DomainProgram]:
        """Get all programs ordered by name."""
        orm_programs = ORMProgram.objects.all().order_by("program_name")
        return [self._to_domain(p) for p in orm_programs]

    def list_by_department(self, department_name: str) -> Iterable[DomainProgram]:
        """Get all programs in a department."""
        orm_programs = ORMProgram.objects.filter(department_name=department_name).order_by("program_name")
        return [self._to_domain(p) for p in orm_programs]

    def list_with_streams(self) -> Iterable[DomainProgram]:
        """Get programs that have streams enabled."""
        orm_programs = ORMProgram.objects.filter(has_streams=True).order_by("program_name")
        return [self._to_domain(p) for p in orm_programs]

    def list_without_streams(self) -> Iterable[DomainProgram]:
        """Get programs without streams."""
        orm_programs = ORMProgram.objects.filter(has_streams=False).order_by("program_name")
        return [self._to_domain(p) for p in orm_programs]

    def create(self, data: dict) -> DomainProgram:
        """Create new program."""
        orm_program = ORMProgram.objects.create(**data)
        return self._to_domain(orm_program)

    def update(self, program_id: int, data: dict) -> DomainProgram:
        """Update program fields."""
        orm_program = ORMProgram.objects.get(program_id=program_id)
        for key, value in data.items():
            setattr(orm_program, key, value)
        orm_program.save()
        return self._to_domain(orm_program)

    def delete(self, program_id: int) -> None:
        """Delete program (cascades to streams and courses)."""
        orm_program = ORMProgram.objects.get(program_id=program_id)
        orm_program.delete()

    def can_be_deleted(self, program_id: int) -> bool:
        """Check if program can be safely deleted (no students or courses)."""
        orm_program = ORMProgram.objects.get(program_id=program_id)
        # Note: students is a reverse relation from user_management context
        has_students = hasattr(orm_program, 'students') and orm_program.students.exists()
        has_courses = orm_program.courses.exists()
        return not (has_students or has_courses)

    def students_count(self, program_id: int) -> int:
        """Count students enrolled in this program."""
        orm_program = ORMProgram.objects.get(program_id=program_id)
        if hasattr(orm_program, 'students'):
            return orm_program.students.count()
        return 0

    def courses_count(self, program_id: int) -> int:
        """Count courses in this program."""
        orm_program = ORMProgram.objects.get(program_id=program_id)
        return orm_program.courses.count()
