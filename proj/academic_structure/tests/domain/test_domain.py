"""Comprehensive domain tests for academic_structure."""

import pytest

from academic_structure.domain.value_objects import ProgramCode, CourseCode
from academic_structure.domain.entities.program import Program
from academic_structure.domain.entities.stream import Stream
from academic_structure.domain.entities.course import Course
from academic_structure.domain.services.program_service import ProgramService
from academic_structure.domain.services.stream_service import StreamService
from academic_structure.domain.services.course_service import CourseService
from academic_structure.domain.exceptions import (
    ValidationError,
    ProgramCodeAlreadyExistsError,
    ProgramCannotBeDeletedError,
    StreamNotAllowedError,
    StreamAlreadyExistsError,
    StreamCannotBeDeletedError,
    CourseCodeAlreadyExistsError,
    CourseCannotBeDeletedError,
)


# ============================================================================
# VALUE OBJECT TESTS
# ============================================================================

def test_program_code_valid():
    """Test ProgramCode accepts valid 3-letter codes."""
    pc = ProgramCode("bcs")
    assert pc.code == "BCS"


@pytest.mark.parametrize("bad", ["BC", "abcd", "12A", "b1c"])
def test_program_code_invalid(bad):
    """Test ProgramCode rejects invalid formats."""
    with pytest.raises(Exception):
        ProgramCode(bad)


def test_course_code_valid():
    """Test CourseCode accepts valid pattern."""
    cc = CourseCode("cs201")
    assert cc.code == "CS201"


@pytest.mark.parametrize("bad", ["C201", "CS20", "cs2010", "12345"])
def test_course_code_invalid(bad):
    """Test CourseCode rejects invalid formats."""
    with pytest.raises(Exception):
        CourseCode(bad)


# ============================================================================
# ENTITY TESTS
# ============================================================================

def test_program_entity_creation():
    """Test Program entity instantiation."""
    program = Program(
        program_id=1,
        program_name="BSc Computer Science",
        program_code="BCS",
        department_name="Computer Science",
        has_streams=True,
    )
    assert program.program_code == "BCS"
    assert program.requires_streams() is True
    assert str(program) == "BCS - BSc Computer Science"


def test_stream_entity_creation():
    """Test Stream entity instantiation."""
    stream = Stream(
        stream_id=1,
        stream_name="A",
        program_id=5,
        year_of_study=2,
    )
    assert stream.year_of_study == 2
    assert "Year 2" in str(stream)


def test_course_entity_creation():
    """Test Course entity instantiation."""
    course = Course(
        course_id=1,
        course_name="Data Structures",
        course_code="CS201",
        program_id=5,
        department_name="Computer Science",
        lecturer_id=None,
    )
    assert course.is_assigned_to_lecturer() is False
    assert str(course) == "CS201 - Data Structures"

    course_with_lecturer = Course(
        course_id=2,
        course_name="Algorithms",
        course_code="CS202",
        program_id=5,
        department_name="Computer Science",
        lecturer_id=10,
    )
    assert course_with_lecturer.is_assigned_to_lecturer() is True


# ============================================================================
# PROGRAM SERVICE TESTS
# ============================================================================

class FakeProgramRepo:
    """Mock repository for testing ProgramService."""
    
    def __init__(self):
        self.programs = {}
        self.codes = set()
        self.next_id = 1
    
    def students_count(self, program_id: int) -> int:
        return 0
    
    def courses_count(self, program_id: int) -> int:
        return 0
    
    def exists_by_code(self, code: str) -> bool:
        return code.upper() in self.codes
    
    def get_by_id(self, program_id: int):
        return self.programs.get(program_id)


def test_program_service_can_be_deleted_when_no_deps():
    """Test program can be deleted when no students/courses."""
    repo = FakeProgramRepo()
    service = ProgramService(repo)
    
    program = Program(
        program_id=1,
        program_name="Test",
        program_code="TST",
        department_name="Dept",
    )
    assert service.can_be_deleted(program) is True


def test_program_service_cannot_be_deleted_with_students():
    """Test program cannot be deleted when students exist."""
    repo = FakeProgramRepo()
    repo.students_count = lambda pid: 2  # Override to return students
    service = ProgramService(repo)
    
    program = Program(
        program_id=1,
        program_name="Test",
        program_code="TST",
        department_name="Dept",
    )
    assert service.can_be_deleted(program) is False


def test_program_service_validate_code():
    """Test program code validation."""
    repo = FakeProgramRepo()
    service = ProgramService(repo)
    
    # Valid codes
    assert service.validate_program_code("bcs") == "BCS"
    assert service.validate_program_code("IT") == "IT"
    
    # Invalid codes
    with pytest.raises(ValidationError):
        service.validate_program_code("A")  # Too short
    
    with pytest.raises(ValidationError):
        service.validate_program_code("TOOLONG")  # Too long
    
    with pytest.raises(ValidationError):
        service.validate_program_code("")  # Empty


def test_program_service_validate_for_creation():
    """Test program creation validation."""
    repo = FakeProgramRepo()
    service = ProgramService(repo)
    
    # Valid data
    data = {
        "program_code": "BCS",
        "program_name": "BSc Computer Science",
        "department_name": "Computer Science",
        "has_streams": True,
    }
    service.validate_program_for_creation(data)  # Should not raise
    
    # Duplicate code
    repo.codes.add("BCS")
    with pytest.raises(ProgramCodeAlreadyExistsError):
        service.validate_program_for_creation(data)
    
    # Invalid name
    repo.codes.clear()
    data["program_name"] = "AB"  # Too short
    with pytest.raises(ValidationError):
        service.validate_program_for_creation(data)


# ============================================================================
# STREAM SERVICE TESTS
# ============================================================================

class FakeStreamRepo:
    """Mock repository for testing StreamService."""
    
    def __init__(self):
        self.streams = {}
        self.next_id = 1
    
    def students_count(self, stream_id: int) -> int:
        return 0
    
    def exists_by_program_and_name(
        self, program_id: int, stream_name: str, year_of_study: int
    ) -> bool:
        return False
    
    def get_by_id(self, stream_id: int):
        return self.streams.get(stream_id)


def test_stream_service_validate_year():
    """Test year of study validation."""
    repo = FakeStreamRepo()
    prog_repo = FakeProgramRepo()
    service = StreamService(repo, prog_repo)
    
    # Valid years
    service.validate_year_of_study(1)
    service.validate_year_of_study(4)
    
    # Invalid years
    with pytest.raises(ValidationError):
        service.validate_year_of_study(0)
    
    with pytest.raises(ValidationError):
        service.validate_year_of_study(5)
    
    with pytest.raises(ValidationError):
        service.validate_year_of_study("two")  # Not an int


def test_stream_service_validate_for_creation_requires_has_streams():
    """Test stream creation requires program.has_streams=True."""
    repo = FakeStreamRepo()
    prog_repo = FakeProgramRepo()
    service = StreamService(repo, prog_repo)
    
    # Program without streams
    program_no_streams = Program(
        program_id=1,
        program_name="Test",
        program_code="TST",
        department_name="Dept",
        has_streams=False,
    )
    prog_repo.programs[1] = program_no_streams
    
    with pytest.raises(StreamNotAllowedError):
        service.validate_stream_for_creation(1, "A", 2)
    
    # Program with streams enabled
    program_with_streams = Program(
        program_id=2,
        program_name="Test 2",
        program_code="TS2",
        department_name="Dept",
        has_streams=True,
    )
    prog_repo.programs[2] = program_with_streams
    
    # Should not raise
    service.validate_stream_for_creation(2, "A", 2)


def test_stream_service_can_be_deleted():
    """Test stream deletion rules."""
    repo = FakeStreamRepo()
    prog_repo = FakeProgramRepo()
    service = StreamService(repo, prog_repo)
    
    stream = Stream(
        stream_id=1,
        stream_name="A",
        program_id=1,
        year_of_study=2,
    )
    
    # No students - can delete
    assert service.can_be_deleted(stream) is True
    
    # With students - cannot delete
    repo.students_count = lambda sid: 5
    assert service.can_be_deleted(stream) is False


# ============================================================================
# COURSE SERVICE TESTS
# ============================================================================

class FakeCourseRepo:
    """Mock repository for testing CourseService."""
    
    def __init__(self):
        self.courses = {}
        self.codes = set()
        self.next_id = 1
    
    def sessions_count(self, course_id: int) -> int:
        return 0
    
    def exists_by_code(self, code: str) -> bool:
        return code.upper() in self.codes
    
    def get_by_id(self, course_id: int):
        return self.courses.get(course_id)


def test_course_service_validate_code():
    """Test course code validation."""
    repo = FakeCourseRepo()
    prog_repo = FakeProgramRepo()
    service = CourseService(repo, prog_repo)
    
    # Valid codes
    assert service.validate_course_code("cs201") == "CS201"
    assert service.validate_course_code("ENG301") == "ENG301"
    
    # Invalid codes
    with pytest.raises(ValidationError):
        service.validate_course_code("CS")  # Too short
    
    with pytest.raises(ValidationError):
        service.validate_course_code("12345")  # No letters
    
    with pytest.raises(ValidationError):
        service.validate_course_code("ABCD")  # No digits


def test_course_service_validate_for_creation():
    """Test course creation validation."""
    repo = FakeCourseRepo()
    prog_repo = FakeProgramRepo()
    prog_repo.programs[1] = Program(
        program_id=1,
        program_name="Test",
        program_code="TST",
        department_name="Dept",
    )
    prog_repo.exists_by_id = lambda pid: pid == 1
    
    service = CourseService(repo, prog_repo)
    
    # Valid data
    data = {
        "course_code": "CS201",
        "course_name": "Data Structures",
        "program_id": 1,
        "department_name": "Computer Science",
    }
    service.validate_course_for_creation(data)  # Should not raise
    
    # Duplicate code
    repo.codes.add("CS201")
    with pytest.raises(CourseCodeAlreadyExistsError):
        service.validate_course_for_creation(data)
    
    # Invalid program
    repo.codes.clear()
    data["program_id"] = 999
    with pytest.raises(Exception):  # ProgramNotFoundError or validation error
        service.validate_course_for_creation(data)


def test_course_service_can_be_deleted():
    """Test course deletion rules."""
    repo = FakeCourseRepo()
    prog_repo = FakeProgramRepo()
    service = CourseService(repo, prog_repo)
    
    course = Course(
        course_id=1,
        course_name="Test",
        course_code="TST101",
        program_id=1,
        department_name="Dept",
    )
    
    # No sessions - can delete
    assert service.can_be_deleted(course) is True
    
    # With sessions - cannot delete
    repo.sessions_count = lambda cid: 3
    assert service.can_be_deleted(course) is False

