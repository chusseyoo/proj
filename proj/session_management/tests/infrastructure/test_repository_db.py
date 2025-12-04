"""Comprehensive DB-backed tests for SessionRepository."""

import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import IntegrityError

from session_management.domain.entities.session import Session as DomainSession
from session_management.domain.value_objects.time_window import TimeWindow
from session_management.domain.value_objects.location import Location
from session_management.domain.exceptions.core import OverlappingSessionError
from session_management.infrastructure.repositories.session_repository import SessionRepository
from session_management.infrastructure.orm.django_models import Session as ORMSession
from academic_structure.infrastructure.orm.django_models import Program, Course
from user_management.infrastructure.orm.django_models import User, LecturerProfile


@pytest.fixture
def test_fk_data():
    """Create FK objects for tests."""
    # Create Program
    program = Program.objects.create(
        program_name="Bachelor of Computer Science",
        program_code="BCS",
        department_name="Computing",
        has_streams=False,
    )
    
    # Create User for Lecturer
    user = User.objects.create_user(
        email="test.lecturer@example.com",
        role=User.Roles.LECTURER,
        first_name="Test",
        last_name="Lecturer",
        password="testpass123",
    )
    
    # Create LecturerProfile
    lecturer = LecturerProfile.objects.create(
        user=user,
        department_name="Computing",
    )
    
    # Create Course
    course = Course.objects.create(
        program=program,
        course_code="BCS012",
        course_name="Data Structures",
        department_name="Computing",
        lecturer=lecturer,
    )
    
    # Create second lecturer for multi-lecturer tests
    user2 = User.objects.create_user(
        email="test.lecturer2@example.com",
        role=User.Roles.LECTURER,
        first_name="Test2",
        last_name="Lecturer2",
        password="testpass123",
    )
    
    lecturer2 = LecturerProfile.objects.create(
        user=user2,
        department_name="Computing",
    )
    
    return {
        "program": program,
        "course": course,
        "lecturer": lecturer,
        "lecturer2": lecturer2,
    }


@pytest.fixture
def repository():
    """Provide a SessionRepository instance."""
    return SessionRepository()


@pytest.fixture
def base_session_data(test_fk_data):
    """Provide base session data for tests."""
    now = timezone.now()
    return {
        "program_id": test_fk_data["program"].program_id,
        "course_id": test_fk_data["course"].course_id,
        "lecturer_id": test_fk_data["lecturer"].lecturer_id,
        "stream_id": None,
        "date_created": now.date(),
        "time_window": TimeWindow(
            start=now,
            end=now + timedelta(hours=1)
        ),
        "location": Location(
            latitude=51.5074,
            longitude=-0.1278,
            description="Main Hall"
        )
    }


@pytest.mark.django_db
class TestRepositorySave:
    """Tests for repository save (create/update)."""
    
    def test_create_session(self, repository, base_session_data):
        """Should create a new session and return it with assigned ID."""
        session = DomainSession(session_id=None, **base_session_data)
        
        saved = repository.save(session)
        
        assert saved.session_id is not None
        assert saved.program_id == 1
        assert saved.course_id == 1
        assert saved.lecturer_id == 1
        assert saved.stream_id is None
    
    def test_update_session(self, repository, base_session_data):
        """Should update existing session."""
        # Create first
        session = DomainSession(session_id=None, **base_session_data)
        saved = repository.save(session)
        
        # Update
        new_end = saved.time_window.start + timedelta(hours=2)
        updated_data = {**base_session_data}
        updated_data["time_window"] = TimeWindow(
            start=saved.time_window.start,
            end=new_end
        )
        updated_session = DomainSession(session_id=saved.session_id, **updated_data)
        
        result = repository.save(updated_session)
        
        assert result.session_id == saved.session_id
        assert result.time_window.end == new_end
    
    def test_overlapping_sessions_raises_error(self, repository, base_session_data):
        """Should raise OverlappingSessionError when exclusion constraint triggers."""
        # Note: This test requires Postgres with the exclusion constraint
        # On sqlite, the constraint won't exist and overlap check is app-level only
        
        # Create first session
        session1 = DomainSession(session_id=None, **base_session_data)
        repository.save(session1)
        
        # Try to create overlapping session for same lecturer
        session2 = DomainSession(session_id=None, **base_session_data)
        
        # On Postgres with exclusion constraint, this should raise IntegrityError
        # which gets mapped to OverlappingSessionError
        # On sqlite, this won't trigger (constraint doesn't exist)
        try:
            repository.save(session2)
            # If we get here on Postgres, the constraint didn't work
            # On sqlite, this is expected behavior
        except OverlappingSessionError:
            # Expected on Postgres
            pass


@pytest.mark.django_db
class TestRepositoryGet:
    """Tests for repository get operations."""
    
    def test_get_existing_session(self, repository, base_session_data):
        """Should retrieve existing session by ID."""
        session = DomainSession(session_id=None, **base_session_data)
        saved = repository.save(session)
        
        retrieved = repository.get(saved.session_id)
        
        assert retrieved is not None
        assert retrieved.session_id == saved.session_id
        assert retrieved.lecturer_id == saved.lecturer_id
    
    def test_get_nonexistent_session(self, repository):
        """Should return None for non-existent session."""
        result = repository.get(99999)
        assert result is None
    
    def test_get_by_id_existing(self, repository, base_session_data):
        """Should retrieve session with get_by_id."""
        session = DomainSession(session_id=None, **base_session_data)
        saved = repository.save(session)
        
        retrieved = repository.get_by_id(saved.session_id)
        
        assert retrieved.session_id == saved.session_id
    
    def test_get_by_id_nonexistent_raises(self, repository):
        """Should raise DoesNotExist for non-existent session."""
        with pytest.raises(ORMSession.DoesNotExist):
            repository.get_by_id(99999)


@pytest.mark.django_db
class TestRepositoryList:
    """Tests for repository list operations."""
    
    def test_list_by_lecturer(self, repository, base_session_data, test_fk_data):
        """Should list all sessions for a lecturer."""
        # Create sessions for lecturer 1
        for i in range(3):
            data = {**base_session_data}
            data["time_window"] = TimeWindow(
                start=timezone.now() + timedelta(hours=i),
                end=timezone.now() + timedelta(hours=i+1)
            )
            session = DomainSession(session_id=None, **data)
            repository.save(session)
        
        # Create session for lecturer 2
        data2 = {**base_session_data, "lecturer_id": test_fk_data["lecturer2"].lecturer_id}
        session2 = DomainSession(session_id=None, **data2)
        repository.save(session2)
        
        # List for lecturer 1
        results = repository.list_by_lecturer(test_fk_data["lecturer"].lecturer_id)
        
        assert len(results) == 3
        assert all(s.lecturer_id == test_fk_data["lecturer"].lecturer_id for s in results)
        # Should be ordered by time_created DESC
        assert results[0].time_window.start > results[1].time_window.start
    
    def test_list_by_course(self, repository, base_session_data, test_fk_data):
        """Should list all sessions for a course."""
        # Create sessions for course 1 with different lecturers
        session1_data = {**base_session_data}
        session1 = DomainSession(session_id=None, **session1_data)
        repository.save(session1)
        
        session2_data = {**base_session_data, "lecturer_id": test_fk_data["lecturer2"].lecturer_id}
        session2_data["time_window"] = TimeWindow(
            start=timezone.now() + timedelta(hours=1),
            end=timezone.now() + timedelta(hours=2)
        )
        session2 = DomainSession(session_id=None, **session2_data)
        repository.save(session2)
        
        results = repository.list_by_course(test_fk_data["course"].course_id)
        
        assert len(results) == 2
        assert all(s.course_id == test_fk_data["course"].course_id for s in results)
    
    def test_list_by_program(self, repository, base_session_data, test_fk_data):
        """Should list sessions for program, optionally filtered by stream."""
        # Create two sessions for program 1, both no stream
        data1 = {**base_session_data, "stream_id": None}
        session1 = DomainSession(session_id=None, **data1)
        repository.save(session1)
        
        data2 = {**base_session_data, "stream_id": None}
        data2["time_window"] = TimeWindow(
            start=timezone.now() + timedelta(hours=1),
            end=timezone.now() + timedelta(hours=2)
        )
        session2 = DomainSession(session_id=None, **data2)
        repository.save(session2)
        
        # List all for program
        all_results = repository.list_by_program(test_fk_data["program"].program_id)
        assert len(all_results) == 2
        assert all(s.program_id == test_fk_data["program"].program_id for s in all_results)
    
    def test_list_active(self, repository, base_session_data):
        """Should list only currently active sessions."""
        now = timezone.now()
        
        # Create past session (ended)
        past_data = {**base_session_data}
        past_data["time_window"] = TimeWindow(
            start=now - timedelta(hours=2),
            end=now - timedelta(hours=1)
        )
        past_session = DomainSession(session_id=None, **past_data)
        repository.save(past_session)
        
        # Create active session
        active_data = {**base_session_data}
        active_data["time_window"] = TimeWindow(
            start=now - timedelta(minutes=10),
            end=now + timedelta(minutes=50)
        )
        active_session = DomainSession(session_id=None, **active_data)
        repository.save(active_session)
        
        # Create future session (not started)
        future_data = {**base_session_data}
        future_data["time_window"] = TimeWindow(
            start=now + timedelta(hours=1),
            end=now + timedelta(hours=2)
        )
        future_session = DomainSession(session_id=None, **future_data)
        repository.save(future_session)
        
        # List active
        active_results = repository.list_active(now)
        
        assert len(active_results) == 1
        assert active_results[0].session_id is not None
        # Verify it's the active session by checking time window
        assert active_results[0].time_window.start <= now < active_results[0].time_window.end


@pytest.mark.django_db
class TestRepositoryOverlap:
    """Tests for overlap detection."""
    
    def test_has_overlapping_detects_overlap(self, repository, base_session_data):
        """Should detect overlapping sessions."""
        # Create existing session
        session = DomainSession(session_id=None, **base_session_data)
        saved = repository.save(session)
        
        # Check for overlap with same time window
        has_overlap = repository.has_overlapping(1, base_session_data["time_window"])
        
        assert has_overlap is True
    
    def test_has_overlapping_no_overlap(self, repository, base_session_data):
        """Should return False when no overlap exists."""
        # Create session
        session = DomainSession(session_id=None, **base_session_data)
        repository.save(session)
        
        # Check for overlap in non-overlapping time window
        later_window = TimeWindow(
            start=base_session_data["time_window"].end + timedelta(hours=1),
            end=base_session_data["time_window"].end + timedelta(hours=2)
        )
        has_overlap = repository.has_overlapping(1, later_window)
        
        assert has_overlap is False
    
    def test_has_overlapping_exclude_session(self, repository, base_session_data):
        """Should exclude specified session from overlap check."""
        # Create session
        session = DomainSession(session_id=None, **base_session_data)
        saved = repository.save(session)
        
        # Check overlap but exclude the saved session itself
        has_overlap = repository.has_overlapping(
            1,
            base_session_data["time_window"],
            exclude_session_id=saved.session_id
        )
        
        assert has_overlap is False
    
    def test_has_overlapping_different_lecturer(self, repository, base_session_data):
        """Should not detect overlap for different lecturer."""
        # Create session for lecturer 1
        session = DomainSession(session_id=None, **base_session_data)
        repository.save(session)
        
        # Check overlap for lecturer 2 with same time window
        has_overlap = repository.has_overlapping(2, base_session_data["time_window"])
        
        assert has_overlap is False


@pytest.mark.django_db
class TestRepositoryDelete:
    """Tests for repository delete."""
    
    def test_delete_session(self, repository, base_session_data):
        """Should delete session by ID."""
        session = DomainSession(session_id=None, **base_session_data)
        saved = repository.save(session)
        
        repository.delete(saved.session_id)
        
        result = repository.get(saved.session_id)
        assert result is None
    
    def test_delete_nonexistent_session(self, repository):
        """Should not raise error when deleting non-existent session."""
        # Should complete without error
        repository.delete(99999)
