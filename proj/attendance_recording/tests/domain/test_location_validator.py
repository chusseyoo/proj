import pytest

from attendance_recording.domain.services.location_validator import LocationValidator
from attendance_recording.domain.exceptions import InvalidCoordinatesError


class TestLocationValidator:
    def test_validate_coordinates_success(self):
        coord = LocationValidator.validate_coordinates(10.0, 20.0)
        assert coord.latitude == 10.0
        assert coord.longitude == 20.0

    def test_validate_coordinates_invalid_raises(self):
        with pytest.raises(InvalidCoordinatesError):
            LocationValidator.validate_coordinates(100.0, 0.0)

    def test_check_within_radius_true(self):
        session_loc = (0.0, 0.0)
        student_loc = (0.0001, 0.0001)  # about 15m away
        assert LocationValidator.check_within_radius(session_loc, student_loc) is True

    def test_check_within_radius_false(self):
        session_loc = (0.0, 0.0)
        student_loc = (1.0, 1.0)  # far away
        assert LocationValidator.check_within_radius(session_loc, student_loc) is False

    def test_get_distance(self):
        session_loc = (0.0, 0.0)
        student_loc = (0.0, 0.001)  # ~111m
        distance = LocationValidator.get_distance(session_loc, student_loc)
        assert distance > 100
