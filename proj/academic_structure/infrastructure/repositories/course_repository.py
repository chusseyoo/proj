"""Course repository implementation using Django ORM."""

from typing import Optional, Iterable

from ...domain.entities.course import Course as DomainCourse
from ...domain.ports.course_repository import CourseRepositoryPort
from ..orm.django_models import Course as ORMCourse


class CourseRepository:
    """ORM-backed implementation of CourseRepositoryPort."""

    def _to_domain(self, orm_course: ORMCourse) -> DomainCourse:
        """Convert ORM model to domain entity."""
        return DomainCourse(
            course_id=orm_course.course_id,
            course_name=orm_course.course_name,
            course_code=orm_course.course_code,
            program_id=orm_course.program_id,
            department_name=orm_course.department_name,
            lecturer_id=orm_course.lecturer_id,
        )

    def _to_orm_data(self, domain_course: DomainCourse) -> dict:
        """Convert domain entity to ORM data dict."""
        data = {
            "course_name": domain_course.course_name,
            "course_code": domain_course.course_code,
            "program_id": domain_course.program_id,
            "department_name": domain_course.department_name,
            "lecturer_id": domain_course.lecturer_id,
        }
        if domain_course.course_id is not None:
            data["course_id"] = domain_course.course_id
        return data

    def get_by_id(self, course_id: int) -> DomainCourse:
        """Get course by ID. Raises Course.DoesNotExist if not found."""
        orm_course = ORMCourse.objects.select_related("program", "lecturer").get(course_id=course_id)
        return self._to_domain(orm_course)

    def find_by_id(self, course_id: int) -> Optional[DomainCourse]:
        """Get course by ID, return None if not found."""
        try:
            return self.get_by_id(course_id)
        except ORMCourse.DoesNotExist:
            return None

    def get_by_code(self, course_code: str) -> DomainCourse:
        """Get course by code (case-insensitive). Raises if not found."""
        orm_course = ORMCourse.objects.select_related("program", "lecturer").get(
            course_code__iexact=course_code
        )
        return self._to_domain(orm_course)

    def exists_by_code(self, course_code: str) -> bool:
        """Check if course code already exists."""
        return ORMCourse.objects.filter(course_code__iexact=course_code).exists()

    def list_by_program(self, program_id: int) -> Iterable[DomainCourse]:
        """Get all courses for a program."""
        orm_courses = ORMCourse.objects.filter(program_id=program_id).order_by("course_code")
        return [self._to_domain(c) for c in orm_courses]

    def list_by_lecturer(self, lecturer_id: int) -> Iterable[DomainCourse]:
        """Get all courses assigned to a lecturer."""
        orm_courses = ORMCourse.objects.filter(lecturer_id=lecturer_id).order_by("course_code")
        return [self._to_domain(c) for c in orm_courses]

    def list_unassigned(self) -> Iterable[DomainCourse]:
        """Get all courses with no assigned lecturer."""
        orm_courses = ORMCourse.objects.filter(lecturer__isnull=True).order_by("course_code")
        return [self._to_domain(c) for c in orm_courses]

    def create(self, data: dict) -> DomainCourse:
        """Create new course."""
        orm_course = ORMCourse.objects.create(**data)
        return self._to_domain(orm_course)

    def update(self, course_id: int, data: dict) -> DomainCourse:
        """Update course fields."""
        orm_course = ORMCourse.objects.get(course_id=course_id)
        for key, value in data.items():
            setattr(orm_course, key, value)
        orm_course.save()
        return self._to_domain(orm_course)

    def assign_lecturer(self, course_id: int, lecturer_id: int) -> DomainCourse:
        """Assign lecturer to course."""
        orm_course = ORMCourse.objects.get(course_id=course_id)
        orm_course.lecturer_id = lecturer_id
        orm_course.save()
        return self._to_domain(orm_course)

    def unassign_lecturer(self, course_id: int) -> DomainCourse:
        """Remove lecturer from course (set to NULL)."""
        orm_course = ORMCourse.objects.get(course_id=course_id)
        orm_course.lecturer_id = None
        orm_course.save()
        return self._to_domain(orm_course)

    def delete(self, course_id: int) -> None:
        """Delete course."""
        orm_course = ORMCourse.objects.get(course_id=course_id)
        orm_course.delete()

    def can_be_deleted(self, course_id: int) -> bool:
        """Check if course can be safely deleted (no sessions exist)."""
        orm_course = ORMCourse.objects.get(course_id=course_id)
        # Note: sessions is a reverse relation from session_management context
        if hasattr(orm_course, 'sessions'):
            return not orm_course.sessions.exists()
        return True

    def sessions_count(self, course_id: int) -> int:
        """Count sessions for this course."""
        orm_course = ORMCourse.objects.get(course_id=course_id)
        if hasattr(orm_course, 'sessions'):
            return orm_course.sessions.count()
        return 0
