"""Session repository implementation."""

from datetime import datetime
from typing import List, Optional

from django.db.models import Q

from ...domain.entities.session import Session as DomainSession
from ...domain.value_objects.time_window import TimeWindow
from ...domain.value_objects.location import Location
from ..orm.django_models import Session as ORMSession


class SessionRepository:
    """ORM-backed implementation of SessionRepositoryPort."""

    def _to_domain(self, orm_session: ORMSession) -> DomainSession:
        """Convert ORM Session to domain Session entity."""
        time_window = TimeWindow(
            start=orm_session.time_created,
            end=orm_session.time_ended,
        )
        location = Location(
            latitude=float(orm_session.latitude),
            longitude=float(orm_session.longitude),
            description=orm_session.location_description,
        )
        return DomainSession(
            session_id=orm_session.session_id,
            program_id=orm_session.program_id,
            course_id=orm_session.course_id,
            lecturer_id=orm_session.lecturer_id,
            stream_id=orm_session.stream_id,
            date_created=orm_session.date_created,
            time_window=time_window,
            location=location,
        )

    def _to_orm_data(self, session: DomainSession) -> dict:
        """Convert domain Session to ORM data dict."""
        return {
            "program_id": session.program_id,
            "course_id": session.course_id,
            "lecturer_id": session.lecturer_id,
            "stream_id": session.stream_id,
            "time_created": session.time_window.start,
            "time_ended": session.time_window.end,
            "latitude": session.location.latitude,
            "longitude": session.location.longitude,
            "location_description": session.location.description,
        }

    def save(self, session: DomainSession) -> DomainSession:
        """Save session (create or update)."""
        data = self._to_orm_data(session)
        
        if session.session_id is None:
            # Create new session
            orm_session = ORMSession.objects.create(**data)
        else:
            # Update existing session
            orm_session = ORMSession.objects.get(session_id=session.session_id)
            for key, value in data.items():
                setattr(orm_session, key, value)
            orm_session.save()
        
        return self._to_domain(orm_session)

    def get(self, session_id: int) -> Optional[DomainSession]:
        """Get session by ID."""
        try:
            orm_session = ORMSession.objects.select_related(
                "program", "course", "lecturer", "stream"
            ).get(session_id=session_id)
            return self._to_domain(orm_session)
        except ORMSession.DoesNotExist:
            return None

    def get_by_id(self, session_id: int) -> DomainSession:
        """Get session by ID (raises if not found)."""
        orm_session = ORMSession.objects.select_related(
            "program", "course", "lecturer", "stream"
        ).get(session_id=session_id)
        return self._to_domain(orm_session)

    def list_by_lecturer(
        self,
        lecturer_id: int,
        *,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[DomainSession]:
        """List sessions by lecturer, optionally filtered by time range."""
        qs = ORMSession.objects.filter(lecturer_id=lecturer_id)
        
        if start:
            qs = qs.filter(time_created__gte=start)
        if end:
            qs = qs.filter(time_ended__lte=end)
        
        qs = qs.select_related("program", "course", "lecturer", "stream")
        qs = qs.order_by("-time_created")
        
        return [self._to_domain(orm_session) for orm_session in qs]

    def list_by_course(
        self,
        course_id: int,
        *,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[DomainSession]:
        """List sessions by course, optionally filtered by time range."""
        qs = ORMSession.objects.filter(course_id=course_id)
        
        if start:
            qs = qs.filter(time_created__gte=start)
        if end:
            qs = qs.filter(time_ended__lte=end)
        
        qs = qs.select_related("program", "course", "lecturer", "stream")
        qs = qs.order_by("-time_created")
        
        return [self._to_domain(orm_session) for orm_session in qs]

    def list_by_program(
        self,
        program_id: int,
        *,
        stream_id: Optional[int] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[DomainSession]:
        """List sessions by program/stream, optionally filtered by time range."""
        qs = ORMSession.objects.filter(program_id=program_id)
        
        if stream_id is not None:
            qs = qs.filter(stream_id=stream_id)
        
        if start:
            qs = qs.filter(time_created__gte=start)
        if end:
            qs = qs.filter(time_ended__lte=end)
        
        qs = qs.select_related("program", "course", "lecturer", "stream")
        qs = qs.order_by("-time_created")
        
        return [self._to_domain(orm_session) for orm_session in qs]

    def list_active(self, now: datetime) -> List[DomainSession]:
        """List all currently active sessions."""
        qs = ORMSession.objects.filter(
            time_created__lte=now,
            time_ended__gt=now,
        )
        qs = qs.select_related("program", "course", "lecturer", "stream")
        qs = qs.order_by("-time_created")
        
        return [self._to_domain(orm_session) for orm_session in qs]

    def list_active_by_lecturer(self, lecturer_id: int, now: datetime) -> List[DomainSession]:
        """List active sessions for a specific lecturer."""
        qs = ORMSession.objects.filter(
            lecturer_id=lecturer_id,
            time_created__lte=now,
            time_ended__gt=now,
        )
        qs = qs.select_related("program", "course", "lecturer", "stream")
        qs = qs.order_by("-time_created")
        
        return [self._to_domain(orm_session) for orm_session in qs]

    def has_overlapping(self, lecturer_id: int, time_window: TimeWindow) -> bool:
        """Check if lecturer has any overlapping sessions in the given time window."""
        # Overlap condition: (existing_start < new_end) AND (new_start < existing_end)
        overlapping = ORMSession.objects.filter(
            lecturer_id=lecturer_id,
            time_created__lt=time_window.end,
            time_ended__gt=time_window.start,
        ).exists()
        
        return overlapping

    def delete(self, session_id: int) -> None:
        """Delete session by ID."""
        ORMSession.objects.filter(session_id=session_id).delete()

    def get_eligible_students(self, session: DomainSession) -> List[int]:
        """
        Get list of student IDs eligible for this session.
        
        Students are eligible if:
        - Their program matches session.program_id
        - If session.stream_id is set, their stream must match
        - Their account is active
        """
        from user_management.infrastructure.orm.django_models import StudentProfile
        
        qs = StudentProfile.objects.filter(
            program_id=session.program_id,
            user__is_active=True,
        )
        
        if session.stream_id is not None:
            qs = qs.filter(stream_id=session.stream_id)
        
        return list(qs.values_list("student_id", flat=True))
