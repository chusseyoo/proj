"""Tests for CourseDTO and mapper function."""

import pytest
from academic_structure.domain.entities.course import Course
from academic_structure.application.dto import CourseDTO, to_course_dto


class TestCourseDTO:
    """Test cases for CourseDTO dataclass."""

    def test_course_dto_creation_minimal(self):
        """Test creating a CourseDTO with minimal fields."""
        dto = CourseDTO(
            course_id=1,
            course_code="CS201",
            course_name="Data Structures",
            program_id=1,
            department_name="Computer Science",
            lecturer_id=None,
            program_code=None,
            lecturer_name=None
        )

        assert dto.course_id == 1
        assert dto.course_code == "CS201"
        assert dto.course_name == "Data Structures"
        assert dto.program_id == 1
        assert dto.department_name == "Computer Science"
        assert dto.lecturer_id is None
        assert dto.program_code is None
        assert dto.lecturer_name is None

    def test_course_dto_creation_with_enrichment(self):
        """Test creating a CourseDTO with all enrichment fields."""
        dto = CourseDTO(
            course_id=2,
            course_code="ENG301",
            course_name="Advanced English",
            program_id=2,
            department_name="English",
            lecturer_id=10,
            program_code="ENG",
            lecturer_name="Dr. John Smith"
        )

        assert dto.course_id == 2
        assert dto.course_code == "ENG301"
        assert dto.course_name == "Advanced English"
        assert dto.program_id == 2
        assert dto.department_name == "English"
        assert dto.lecturer_id == 10
        assert dto.program_code == "ENG"
        assert dto.lecturer_name == "Dr. John Smith"

    def test_course_dto_is_mutable_but_shouldnt_be_modified(self):
        """Test that CourseDTO fields can be accessed (DTOs are for transfer, not mutation)."""
        dto = CourseDTO(
            course_id=1,
            course_code="CS101",
            course_name="Intro to CS",
            program_id=1,
            department_name="CS",
            lecturer_id=None,
            program_code=None,
            lecturer_name=None
        )

        # DTOs are not frozen in this implementation, but shouldn't be modified
        assert dto.course_id == 1
        assert dto.course_code == "CS101"


class TestToCourseDtoMapper:
    """Test cases for to_course_dto mapper function."""

    def test_to_course_dto_without_enrichment(self):
        """Test mapper without any enrichment."""
        course = Course(
            course_id=1,
            course_code="CS101",
            course_name="Introduction to Programming",
            program_id=1,
            department_name="Computer Science",
            lecturer_id=None
        )

        dto = to_course_dto(course)

        assert isinstance(dto, CourseDTO)
        assert dto.course_id == course.course_id
        assert dto.course_code == course.course_code
        assert dto.course_name == course.course_name
        assert dto.program_id == course.program_id
        assert dto.department_name == course.department_name
        assert dto.lecturer_id is None
        assert dto.program_code is None
        assert dto.lecturer_name is None

    def test_to_course_dto_with_program_code_enrichment(self):
        """Test mapper with program_code enrichment."""
        course = Course(
            course_id=2,
            course_code="MATH201",
            course_name="Calculus II",
            program_id=3,
            department_name="Mathematics",
            lecturer_id=5
        )

        dto = to_course_dto(course, program_code="MATH")

        assert dto.course_id == course.course_id
        assert dto.program_code == "MATH"
        assert dto.lecturer_name is None

    def test_to_course_dto_with_lecturer_name_enrichment(self):
        """Test mapper with lecturer_name enrichment."""
        course = Course(
            course_id=3,
            course_code="ENG301",
            course_name="Literature",
            program_id=2,
            department_name="English",
            lecturer_id=10
        )

        dto = to_course_dto(course, lecturer_name="Dr. Jane Doe")

        assert dto.course_id == course.course_id
        assert dto.lecturer_id == 10
        assert dto.lecturer_name == "Dr. Jane Doe"
        assert dto.program_code is None

    def test_to_course_dto_with_all_enrichment(self):
        """Test mapper with both program_code and lecturer_name enrichment."""
        course = Course(
            course_id=4,
            course_code="PHY401",
            course_name="Quantum Physics",
            program_id=4,
            department_name="Physics",
            lecturer_id=15
        )

        dto = to_course_dto(
            course,
            program_code="PHY",
            lecturer_name="Prof. Albert Einstein"
        )

        assert dto.course_id == course.course_id
        assert dto.course_code == course.course_code
        assert dto.program_id == course.program_id
        assert dto.lecturer_id == 15
        assert dto.program_code == "PHY"
        assert dto.lecturer_name == "Prof. Albert Einstein"

    def test_to_course_dto_preserves_data_types(self):
        """Test that mapper preserves correct data types."""
        course = Course(
            course_id=100,
            course_code="TEST101",
            course_name="Test Course",
            program_id=10,
            department_name="Testing",
            lecturer_id=20
        )

        dto = to_course_dto(course, program_code="TST", lecturer_name="Test Lecturer")

        assert isinstance(dto.course_id, int)
        assert isinstance(dto.course_code, str)
        assert isinstance(dto.course_name, str)
        assert isinstance(dto.program_id, int)
        assert isinstance(dto.department_name, str)
        assert isinstance(dto.lecturer_id, int)
        assert isinstance(dto.program_code, str)
        assert isinstance(dto.lecturer_name, str)

    def test_to_course_dto_with_unassigned_lecturer(self):
        """Test mapper with course that has no lecturer assigned."""
        course = Course(
            course_id=5,
            course_code="CS999",
            course_name="Unassigned Course",
            program_id=1,
            department_name="Computer Science",
            lecturer_id=None
        )

        dto = to_course_dto(course, program_code="CSC", lecturer_name=None)

        assert dto.lecturer_id is None
        assert dto.lecturer_name is None
        assert dto.program_code == "CSC"
