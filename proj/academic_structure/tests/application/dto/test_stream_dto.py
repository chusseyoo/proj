"""Tests for StreamDTO and mapper function."""

import pytest
from academic_structure.domain.entities.stream import Stream
from academic_structure.application.dto import StreamDTO, to_stream_dto


class TestStreamDTO:
    """Test cases for StreamDTO dataclass."""

    def test_stream_dto_creation_without_program_code(self):
        """Test creating a StreamDTO without program_code."""
        dto = StreamDTO(
            stream_id=1,
            stream_name="Stream A",
            program_id=1,
            year_of_study=2,
            program_code=None
        )

        assert dto.stream_id == 1
        assert dto.stream_name == "Stream A"
        assert dto.program_id == 1
        assert dto.year_of_study == 2
        assert dto.program_code is None

    def test_stream_dto_creation_with_program_code(self):
        """Test creating a StreamDTO with program_code enrichment."""
        dto = StreamDTO(
            stream_id=1,
            stream_name="Stream B",
            program_id=2,
            year_of_study=3,
            program_code="CSC"
        )

        assert dto.stream_id == 1
        assert dto.stream_name == "Stream B"
        assert dto.program_id == 2
        assert dto.year_of_study == 3
        assert dto.program_code == "CSC"

    def test_stream_dto_is_mutable_but_shouldnt_be_modified(self):
        """Test that StreamDTO fields can be accessed (DTOs are for transfer, not mutation)."""
        dto = StreamDTO(
            stream_id=1,
            stream_name="Test Stream",
            program_id=1,
            year_of_study=1,
            program_code=None
        )

        # DTOs are not frozen in this implementation, but shouldn't be modified
        assert dto.stream_id == 1
        assert dto.stream_name == "Test Stream"


class TestToStreamDtoMapper:
    """Test cases for to_stream_dto mapper function."""

    def test_to_stream_dto_without_program_code(self):
        """Test mapper without program_code enrichment."""
        stream = Stream(
            stream_id=1,
            stream_name="Stream A",
            program_id=1,
            year_of_study=2
        )

        dto = to_stream_dto(stream)

        assert isinstance(dto, StreamDTO)
        assert dto.stream_id == stream.stream_id
        assert dto.stream_name == stream.stream_name
        assert dto.program_id == stream.program_id
        assert dto.year_of_study == stream.year_of_study
        assert dto.program_code is None

    def test_to_stream_dto_with_program_code(self):
        """Test mapper with program_code enrichment."""
        stream = Stream(
            stream_id=2,
            stream_name="Stream B",
            program_id=5,
            year_of_study=3
        )

        dto = to_stream_dto(stream, program_code="ENG")

        assert isinstance(dto, StreamDTO)
        assert dto.stream_id == stream.stream_id
        assert dto.stream_name == stream.stream_name
        assert dto.program_id == stream.program_id
        assert dto.year_of_study == stream.year_of_study
        assert dto.program_code == "ENG"

    def test_to_stream_dto_preserves_data_types(self):
        """Test that mapper preserves correct data types."""
        stream = Stream(
            stream_id=100,
            stream_name="Test Stream",
            program_id=10,
            year_of_study=4
        )

        dto = to_stream_dto(stream, program_code="TST")

        assert isinstance(dto.stream_id, int)
        assert isinstance(dto.stream_name, str)
        assert isinstance(dto.program_id, int)
        assert isinstance(dto.year_of_study, int)
        assert isinstance(dto.program_code, str)

    def test_to_stream_dto_with_all_year_values(self):
        """Test mapper with different year_of_study values (1-4)."""
        for year in range(1, 5):
            stream = Stream(
                stream_id=year,
                stream_name=f"Year {year}",
                program_id=1,
                year_of_study=year
            )

            dto = to_stream_dto(stream)

            assert dto.year_of_study == year
