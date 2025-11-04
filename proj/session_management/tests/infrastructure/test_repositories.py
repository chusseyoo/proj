"""Tests for SessionRepository implementation."""

import pytest
from datetime import datetime, timedelta, date
from django.test import TestCase
from django.utils import timezone

from session_management.infrastructure.orm.django_models import Session as ORMSession
from session_management.infrastructure.repositories import SessionRepository
from session_management.domain.entities.session import Session as DomainSession
from session_management.domain.value_objects.time_window import TimeWindow
from session_management.domain.value_objects.location import Location
from academic_structure.infrastructure.orm.django_models import Program, Course
from user_management.infrastructure.orm.django_models import User, LecturerProfile


@pytest.mark.django_db
class TestSessionRepository(TestCase):
    """Tests for SessionRepository."""

    def setUp(self):
        """Set up test fixtures."""
        self.repo = SessionRepository()
        
        # Create test program
        self.program = Program.objects.create(
            program_name="Computer Science Program",
            program_code="BCS",
            department_name="Computer Science",
            has_streams=False,
        )
        
        # Create test lecturer
        self.lecturer_user = User.objects.create_user(
            email="lecturer@test.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            role=User.Roles.LECTURER,
        )
        self.lecturer_profile = LecturerProfile.objects.create(
            user=self.lecturer_user,
            department_name="Computer Science",
        )
        
        # Create test course
        self.course = Course.objects.create(
            course_code="CS101",
            course_name="Introduction to Programming",
            program=self.program,
            department_name="Computer Science",
            lecturer=self.lecturer_profile,
        )

    def test_save_creates_new_session(self):
        """Test creating a new session."""
        now = timezone.now()
        time_window = TimeWindow(
            start=now,
            end=now + timedelta(hours=1),
        )
        location = Location(latitude=1.0, longitude=2.0, description="Room 101")
        
        domain_session = DomainSession(
            session_id=None,
            program_id=self.program.program_id,
            course_id=self.course.course_id,
            lecturer_id=self.lecturer_profile.lecturer_id,
            stream_id=None,
            date_created=date.today(),
            time_window=time_window,
            location=location,
        )
        
        saved_session = self.repo.save(domain_session)
        
        assert saved_session.session_id is not None
        assert saved_session.program_id == self.program.program_id
        assert saved_session.course_id == self.course.course_id
        assert saved_session.lecturer_id == self.lecturer_profile.lecturer_id
        assert saved_session.location.latitude == 1.0
        assert saved_session.location.longitude == 2.0

    def test_get_by_id(self):
        """Test getting session by ID."""
        now = timezone.now()
        orm_session = ORMSession.objects.create(
            program=self.program,
            course=self.course,
            lecturer=self.lecturer_profile,
            time_created=now,
            time_ended=now + timedelta(hours=1),
            latitude=1.0,
            longitude=2.0,
        )
        
        domain_session = self.repo.get_by_id(orm_session.session_id)
        
        assert domain_session.session_id == orm_session.session_id
        assert domain_session.program_id == self.program.program_id
        assert domain_session.course_id == self.course.course_id

    def test_get_returns_none_for_nonexistent(self):
        """Test that get returns None for nonexistent session."""
        result = self.repo.get(99999)
        assert result is None

    def test_list_by_lecturer(self):
        """Test listing sessions by lecturer."""
        now = timezone.now()
        
        # Create two sessions for the same lecturer
        ORMSession.objects.create(
            program=self.program,
            course=self.course,
            lecturer=self.lecturer_profile,
            time_created=now,
            time_ended=now + timedelta(hours=1),
            latitude=1.0,
            longitude=2.0,
        )
        ORMSession.objects.create(
            program=self.program,
            course=self.course,
            lecturer=self.lecturer_profile,
            time_created=now + timedelta(days=1),
            time_ended=now + timedelta(days=1, hours=1),
            latitude=1.0,
            longitude=2.0,
        )
        
        sessions = self.repo.list_by_lecturer(self.lecturer_profile.lecturer_id)
        
        assert len(sessions) == 2
        # Should be ordered by time_created DESC
        assert sessions[0].time_window.start > sessions[1].time_window.start

    def test_list_by_course(self):
        """Test listing sessions by course."""
        now = timezone.now()
        
        ORMSession.objects.create(
            program=self.program,
            course=self.course,
            lecturer=self.lecturer_profile,
            time_created=now,
            time_ended=now + timedelta(hours=1),
            latitude=1.0,
            longitude=2.0,
        )
        
        sessions = self.repo.list_by_course(self.course.course_id)
        
        assert len(sessions) == 1
        assert sessions[0].course_id == self.course.course_id

    def test_list_active(self):
        """Test listing active sessions."""
        now = timezone.now()
        
        # Active session (started in past, ends in future)
        ORMSession.objects.create(
            program=self.program,
            course=self.course,
            lecturer=self.lecturer_profile,
            time_created=now - timedelta(minutes=30),
            time_ended=now + timedelta(minutes=30),
            latitude=1.0,
            longitude=2.0,
        )
        
        # Ended session
        ORMSession.objects.create(
            program=self.program,
            course=self.course,
            lecturer=self.lecturer_profile,
            time_created=now - timedelta(hours=2),
            time_ended=now - timedelta(hours=1),
            latitude=1.0,
            longitude=2.0,
        )
        
        # Future session
        ORMSession.objects.create(
            program=self.program,
            course=self.course,
            lecturer=self.lecturer_profile,
            time_created=now + timedelta(hours=1),
            time_ended=now + timedelta(hours=2),
            latitude=1.0,
            longitude=2.0,
        )
        
        active_sessions = self.repo.list_active(now)
        
        assert len(active_sessions) == 1
        assert active_sessions[0].is_active

    def test_has_overlapping_detects_overlap(self):
        """Test that has_overlapping detects overlapping sessions."""
        now = timezone.now()
        
        # Create existing session: 10:00 - 11:00
        ORMSession.objects.create(
            program=self.program,
            course=self.course,
            lecturer=self.lecturer_profile,
            time_created=now,
            time_ended=now + timedelta(hours=1),
            latitude=1.0,
            longitude=2.0,
        )
        
        # Test overlapping time window: 10:30 - 11:30
        overlapping_window = TimeWindow(
            start=now + timedelta(minutes=30),
            end=now + timedelta(hours=1, minutes=30),
        )
        
        assert self.repo.has_overlapping(
            self.lecturer_profile.lecturer_id,
            overlapping_window
        ) is True

    def test_has_overlapping_no_overlap(self):
        """Test that has_overlapping returns False for non-overlapping sessions."""
        now = timezone.now()
        
        # Create existing session: 10:00 - 11:00
        ORMSession.objects.create(
            program=self.program,
            course=self.course,
            lecturer=self.lecturer_profile,
            time_created=now,
            time_ended=now + timedelta(hours=1),
            latitude=1.0,
            longitude=2.0,
        )
        
        # Test non-overlapping time window: 11:00 - 12:00
        non_overlapping_window = TimeWindow(
            start=now + timedelta(hours=1),
            end=now + timedelta(hours=2),
        )
        
        assert self.repo.has_overlapping(
            self.lecturer_profile.lecturer_id,
            non_overlapping_window
        ) is False

    def test_delete_session(self):
        """Test deleting a session."""
        now = timezone.now()
        orm_session = ORMSession.objects.create(
            program=self.program,
            course=self.course,
            lecturer=self.lecturer_profile,
            time_created=now,
            time_ended=now + timedelta(hours=1),
            latitude=1.0,
            longitude=2.0,
        )
        
        session_id = orm_session.session_id
        self.repo.delete(session_id)
        
        assert not ORMSession.objects.filter(session_id=session_id).exists()

    def test_to_domain_conversion(self):
        """Test ORM to domain entity conversion."""
        now = timezone.now()
        orm_session = ORMSession.objects.create(
            program=self.program,
            course=self.course,
            lecturer=self.lecturer_profile,
            time_created=now,
            time_ended=now + timedelta(hours=1),
            latitude=1.5,
            longitude=2.5,
            location_description="Test Room",
        )
        
        domain_session = self.repo._to_domain(orm_session)
        
        assert isinstance(domain_session, DomainSession)
        assert domain_session.session_id == orm_session.session_id
        assert isinstance(domain_session.time_window, TimeWindow)
        assert isinstance(domain_session.location, Location)
        assert domain_session.location.latitude == 1.5
        assert domain_session.location.description == "Test Room"
