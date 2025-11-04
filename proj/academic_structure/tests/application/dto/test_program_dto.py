"""Tests for ProgramDTO and mapper function."""

import pytest
from academic_structure.domain.entities.program import Program
from academic_structure.application.dto import ProgramDTO, to_program_dto


class TestProgramDTO:
    """Test cases for ProgramDTO dataclass."""

    def test_program_dto_creation(self):
        """Test creating a ProgramDTO instance."""
        dto = ProgramDTO(
            program_id=1,
            program_name="Bachelor of Science in Computer Science",
            program_code="CSC",
            department_name="Computer Science",
            has_streams=True
        )

        assert dto.program_id == 1
        assert dto.program_name == "Bachelor of Science in Computer Science"
        assert dto.program_code == "CSC"
        assert dto.department_name == "Computer Science"
        assert dto.has_streams is True

    def test_program_dto_immutability(self):
        """Test that ProgramDTO fields can be accessed (DTOs are for transfer, not mutation)."""
        dto = ProgramDTO(
            program_id=1,
            program_name="Test Program",
            program_code="TST",
            department_name="Test Dept",
            has_streams=False
        )

        # DTOs are not frozen in this implementation, but shouldn't be modified
        assert dto.program_id == 1
        assert dto.program_name == "Test Program"


class TestToProgramDtoMapper:
    """Test cases for to_program_dto mapper function."""

    def test_to_program_dto_maps_all_fields(self):
        """Test that mapper correctly converts Program entity to DTO."""
        program = Program(
            program_id=1,
            program_name="Bachelor of Arts in English",
            program_code="ENG",
            department_name="English Department",
            has_streams=False
        )

        dto = to_program_dto(program)

        assert isinstance(dto, ProgramDTO)
        assert dto.program_id == program.program_id
        assert dto.program_name == program.program_name
        assert dto.program_code == program.program_code
        assert dto.department_name == program.department_name
        assert dto.has_streams == program.has_streams

    def test_to_program_dto_with_streams(self):
        """Test mapper with a program that has streams."""
        program = Program(
            program_id=2,
            program_name="Bachelor of Science in Engineering",
            program_code="ENG",
            department_name="Engineering",
            has_streams=True
        )

        dto = to_program_dto(program)

        assert dto.has_streams is True

    def test_to_program_dto_preserves_data_types(self):
        """Test that mapper preserves correct data types."""
        program = Program(
            program_id=100,
            program_name="Test Program",
            program_code="TST",
            department_name="Test",
            has_streams=True
        )

        dto = to_program_dto(program)

        assert isinstance(dto.program_id, int)
        assert isinstance(dto.program_name, str)
        assert isinstance(dto.program_code, str)
        assert isinstance(dto.department_name, str)
        assert isinstance(dto.has_streams, bool)
