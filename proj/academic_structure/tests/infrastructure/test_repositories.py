"""Tests for repository implementations."""

import pytest
from django.test import TestCase

from academic_structure.infrastructure.orm.django_models import Program as ORMProgram, Stream as ORMStream, Course as ORMCourse
from academic_structure.infrastructure.repositories import ProgramRepository, StreamRepository, CourseRepository
from academic_structure.domain.entities.program import Program as DomainProgram
from academic_structure.domain.entities.stream import Stream as DomainStream
from academic_structure.domain.entities.course import Course as DomainCourse
from user_management.infrastructure.orm.django_models import User, LecturerProfile


@pytest.mark.django_db
class TestProgramRepository(TestCase):
    """Tests for ProgramRepository."""

    def setUp(self):
        self.repo = ProgramRepository()

    def test_create_program(self):
        """Test creating a program."""
        data = {
            "program_name": "BSc Computer Science",
            "program_code": "BCS",
            "department_name": "Computer Science",
            "has_streams": True,
        }
        program = self.repo.create(data)
        
        assert program.program_id is not None
        assert program.program_name == "BSc Computer Science"
        assert program.program_code == "BCS"
        assert program.has_streams is True

    def test_get_by_id(self):
        """Test getting program by ID."""
        orm_program = ORMProgram.objects.create(
            program_name="Test Program",
            program_code="TST",
            department_name="Test Dept",
            has_streams=False,
        )
        
        program = self.repo.get_by_id(orm_program.program_id)
        assert program.program_code == "TST"
        assert program.program_name == "Test Program"

    def test_get_by_code(self):
        """Test getting program by code (case-insensitive)."""
        ORMProgram.objects.create(
            program_name="Test Program",
            program_code="TST",
            department_name="Test Dept",
        )
        
        program = self.repo.get_by_code("tst")  # lowercase
        assert program.program_code == "TST"

    def test_exists_by_code(self):
        """Test checking if program code exists."""
        ORMProgram.objects.create(
            program_name="Test Program",
            program_code="TST",
            department_name="Test Dept",
        )
        
        assert self.repo.exists_by_code("TST") is True
        assert self.repo.exists_by_code("tst") is True  # case-insensitive
        assert self.repo.exists_by_code("XXX") is False

    def test_list_with_streams(self):
        """Test listing programs with streams."""
        ORMProgram.objects.create(
            program_name="With Streams",
            program_code="WST",
            department_name="Dept",
            has_streams=True,
        )
        ORMProgram.objects.create(
            program_name="Without Streams",
            program_code="WOS",
            department_name="Dept",
            has_streams=False,
        )
        
        programs = list(self.repo.list_with_streams())
        assert len(programs) == 1
        assert programs[0].program_code == "WST"

    def test_update_program(self):
        """Test updating program."""
        orm_program = ORMProgram.objects.create(
            program_name="Old Name",
            program_code="OLD",
            department_name="Old Dept",
        )
        
        updated = self.repo.update(orm_program.program_id, {"program_name": "New Name"})
        assert updated.program_name == "New Name"
        assert updated.program_code == "OLD"  # unchanged

    def test_delete_program(self):
        """Test deleting program."""
        orm_program = ORMProgram.objects.create(
            program_name="To Delete",
            program_code="DEL",
            department_name="Dept",
        )
        
        self.repo.delete(orm_program.program_id)
        assert not ORMProgram.objects.filter(program_id=orm_program.program_id).exists()

    def test_courses_count(self):
        """Test counting courses in program."""
        orm_program = ORMProgram.objects.create(
            program_name="Test Program",
            program_code="TST",
            department_name="Dept",
        )
        ORMCourse.objects.create(
            course_code="CS101",
            course_name="Intro",
            program=orm_program,
            department_name="Dept",
        )
        ORMCourse.objects.create(
            course_code="CS102",
            course_name="Algo",
            program=orm_program,
            department_name="Dept",
        )
        
        count = self.repo.courses_count(orm_program.program_id)
        assert count == 2


@pytest.mark.django_db
class TestStreamRepository(TestCase):
    """Tests for StreamRepository."""

    def setUp(self):
        self.repo = StreamRepository()
        self.program = ORMProgram.objects.create(
            program_name="Test Program",
            program_code="TST",
            department_name="Dept",
            has_streams=True,
        )

    def test_create_stream(self):
        """Test creating a stream."""
        data = {
            "stream_name": "Stream A",
            "program_id": self.program.program_id,
            "year_of_study": 2,
        }
        stream = self.repo.create(data)
        
        assert stream.stream_id is not None
        assert stream.stream_name == "Stream A"
        assert stream.year_of_study == 2

    def test_list_by_program(self):
        """Test listing streams by program."""
        ORMStream.objects.create(
            stream_name="Stream A",
            program=self.program,
            year_of_study=1,
        )
        ORMStream.objects.create(
            stream_name="Stream B",
            program=self.program,
            year_of_study=2,
        )
        
        streams = list(self.repo.list_by_program(self.program.program_id))
        assert len(streams) == 2

    def test_list_by_program_and_year(self):
        """Test filtering streams by year."""
        ORMStream.objects.create(
            stream_name="Year 1 Stream",
            program=self.program,
            year_of_study=1,
        )
        ORMStream.objects.create(
            stream_name="Year 2 Stream",
            program=self.program,
            year_of_study=2,
        )
        
        streams = list(self.repo.list_by_program_and_year(self.program.program_id, 2))
        assert len(streams) == 1
        assert streams[0].year_of_study == 2

    def test_exists_by_program_and_name(self):
        """Test uniqueness check."""
        ORMStream.objects.create(
            stream_name="Stream A",
            program=self.program,
            year_of_study=2,
        )
        
        assert self.repo.exists_by_program_and_name(
            self.program.program_id, "Stream A", 2
        ) is True
        assert self.repo.exists_by_program_and_name(
            self.program.program_id, "Stream B", 2
        ) is False


@pytest.mark.django_db
class TestCourseRepository(TestCase):
    """Tests for CourseRepository."""

    def setUp(self):
        self.repo = CourseRepository()
        self.program = ORMProgram.objects.create(
            program_name="Test Program",
            program_code="TST",
            department_name="Dept",
        )
        
        # Create test lecturer users and profiles
        self.lecturer_user1 = User.objects.create_user(
            email="lecturer1@test.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            role=User.Roles.LECTURER,
        )
        self.lecturer_profile1 = LecturerProfile.objects.create(
            user=self.lecturer_user1,
            department_name="Computer Science",
        )
        
        self.lecturer_user2 = User.objects.create_user(
            email="lecturer2@test.com",
            password="testpass123",
            first_name="Jane",
            last_name="Smith",
            role=User.Roles.LECTURER,
        )
        self.lecturer_profile2 = LecturerProfile.objects.create(
            user=self.lecturer_user2,
            department_name="Computer Science",
        )

    def test_create_course(self):
        """Test creating a course."""
        data = {
            "course_code": "CS201",
            "course_name": "Data Structures",
            "program_id": self.program.program_id,
            "department_name": "Computer Science",
            "lecturer_id": None,
        }
        course = self.repo.create(data)
        
        assert course.course_id is not None
        assert course.course_code == "CS201"
        assert course.lecturer_id is None

    def test_get_by_code(self):
        """Test getting course by code (case-insensitive)."""
        ORMCourse.objects.create(
            course_code="CS201",
            course_name="Data Structures",
            program=self.program,
            department_name="Dept",
        )
        
        course = self.repo.get_by_code("cs201")  # lowercase
        assert course.course_code == "CS201"

    def test_list_unassigned(self):
        """Test listing courses without lecturers."""
        ORMCourse.objects.create(
            course_code="CS201",
            course_name="Assigned Course",
            program=self.program,
            department_name="Dept",
            lecturer=self.lecturer_profile1,  # assigned
        )
        ORMCourse.objects.create(
            course_code="CS202",
            course_name="Unassigned Course",
            program=self.program,
            department_name="Dept",
            lecturer_id=None,
        )
        
        unassigned = list(self.repo.list_unassigned())
        assert len(unassigned) == 1
        assert unassigned[0].course_code == "CS202"

    def test_assign_lecturer(self):
        """Test assigning lecturer to course."""
        orm_course = ORMCourse.objects.create(
            course_code="CS201",
            course_name="Data Structures",
            program=self.program,
            department_name="Dept",
        )
        
        updated = self.repo.assign_lecturer(orm_course.course_id, self.lecturer_profile1.lecturer_id)
        assert updated.lecturer_id == self.lecturer_profile1.lecturer_id

    def test_unassign_lecturer(self):
        """Test removing lecturer from course."""
        orm_course = ORMCourse.objects.create(
            course_code="CS201",
            course_name="Data Structures",
            program=self.program,
            department_name="Dept",
            lecturer=self.lecturer_profile2,
        )
        
        updated = self.repo.unassign_lecturer(orm_course.course_id)
        assert updated.lecturer_id is None
