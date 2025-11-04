"""Stream repository implementation using Django ORM."""

from typing import Optional, Iterable

from ...domain.entities.stream import Stream as DomainStream
from ...domain.ports.stream_repository import StreamRepositoryPort
from ..orm.django_models import Stream as ORMStream


class StreamRepository:
    """ORM-backed implementation of StreamRepositoryPort."""

    def _to_domain(self, orm_stream: ORMStream) -> DomainStream:
        """Convert ORM model to domain entity."""
        return DomainStream(
            stream_id=orm_stream.stream_id,
            stream_name=orm_stream.stream_name,
            program_id=orm_stream.program_id,
            year_of_study=orm_stream.year_of_study,
        )

    def _to_orm_data(self, domain_stream: DomainStream) -> dict:
        """Convert domain entity to ORM data dict."""
        data = {
            "stream_name": domain_stream.stream_name,
            "program_id": domain_stream.program_id,
            "year_of_study": domain_stream.year_of_study,
        }
        if domain_stream.stream_id is not None:
            data["stream_id"] = domain_stream.stream_id
        return data

    def get_by_id(self, stream_id: int) -> DomainStream:
        """Get stream by ID. Raises Stream.DoesNotExist if not found."""
        orm_stream = ORMStream.objects.select_related("program").get(stream_id=stream_id)
        return self._to_domain(orm_stream)

    def find_by_id(self, stream_id: int) -> Optional[DomainStream]:
        """Get stream by ID, return None if not found."""
        try:
            return self.get_by_id(stream_id)
        except ORMStream.DoesNotExist:
            return None

    def list_by_program(self, program_id: int) -> Iterable[DomainStream]:
        """Get all streams for a program, ordered by year and name."""
        orm_streams = ORMStream.objects.filter(program_id=program_id).order_by(
            "year_of_study", "stream_name"
        )
        return [self._to_domain(s) for s in orm_streams]

    def list_by_program_and_year(self, program_id: int, year_of_study: int) -> Iterable[DomainStream]:
        """Get streams for specific program and year."""
        orm_streams = ORMStream.objects.filter(
            program_id=program_id, year_of_study=year_of_study
        ).order_by("stream_name")
        return [self._to_domain(s) for s in orm_streams]

    def exists_by_program_and_name(
        self, program_id: int, stream_name: str, year_of_study: int
    ) -> bool:
        """Check if stream already exists (unique_together constraint)."""
        return ORMStream.objects.filter(
            program_id=program_id, stream_name=stream_name, year_of_study=year_of_study
        ).exists()

    def create(self, data: dict) -> DomainStream:
        """Create new stream."""
        orm_stream = ORMStream.objects.create(**data)
        return self._to_domain(orm_stream)

    def update(self, stream_id: int, data: dict) -> DomainStream:
        """Update stream fields."""
        orm_stream = ORMStream.objects.get(stream_id=stream_id)
        for key, value in data.items():
            setattr(orm_stream, key, value)
        orm_stream.save()
        return self._to_domain(orm_stream)

    def delete(self, stream_id: int) -> None:
        """Delete stream."""
        orm_stream = ORMStream.objects.get(stream_id=stream_id)
        orm_stream.delete()

    def can_be_deleted(self, stream_id: int) -> bool:
        """Check if stream can be safely deleted (no students assigned)."""
        orm_stream = ORMStream.objects.get(stream_id=stream_id)
        # Note: students is a reverse relation from user_management context
        if hasattr(orm_stream, 'students'):
            return not orm_stream.students.exists()
        return True

    def students_count(self, stream_id: int) -> int:
        """Count students assigned to this stream."""
        orm_stream = ORMStream.objects.get(stream_id=stream_id)
        if hasattr(orm_stream, 'students'):
            return orm_stream.students.count()
        return 0
