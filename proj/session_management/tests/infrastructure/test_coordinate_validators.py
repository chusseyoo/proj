"""Tests for coordinate validation utilities."""

import pytest
from session_management.infrastructure.geo_utils.validators import (
    validate_latitude,
    validate_longitude,
    validate_coordinates,
    are_coordinates_equal,
)


class TestLatitudeValidation:
    """Tests for latitude validation."""
    
    def test_valid_latitude(self):
        """Valid latitudes should pass."""
        assert validate_latitude(0.0)
        assert validate_latitude(51.5074)
        assert validate_latitude(-33.8688)
        assert validate_latitude(90.0)
        assert validate_latitude(-90.0)
    
    def test_invalid_latitude_too_high(self):
        """Latitude > 90 should fail."""
        assert not validate_latitude(90.1)
        assert not validate_latitude(100.0)
        assert not validate_latitude(180.0)
    
    def test_invalid_latitude_too_low(self):
        """Latitude < -90 should fail."""
        assert not validate_latitude(-90.1)
        assert not validate_latitude(-100.0)
        assert not validate_latitude(-180.0)
    
    def test_boundary_latitudes(self):
        """Boundary values at exactly ±90 should pass."""
        assert validate_latitude(90.0)
        assert validate_latitude(-90.0)


class TestLongitudeValidation:
    """Tests for longitude validation."""
    
    def test_valid_longitude(self):
        """Valid longitudes should pass."""
        assert validate_longitude(0.0)
        assert validate_longitude(-0.1278)
        assert validate_longitude(151.2093)
        assert validate_longitude(180.0)
        assert validate_longitude(-180.0)
    
    def test_invalid_longitude_too_high(self):
        """Longitude > 180 should fail."""
        assert not validate_longitude(180.1)
        assert not validate_longitude(200.0)
        assert not validate_longitude(360.0)
    
    def test_invalid_longitude_too_low(self):
        """Longitude < -180 should fail."""
        assert not validate_longitude(-180.1)
        assert not validate_longitude(-200.0)
        assert not validate_longitude(-360.0)
    
    def test_boundary_longitudes(self):
        """Boundary values at exactly ±180 should pass."""
        assert validate_longitude(180.0)
        assert validate_longitude(-180.0)


class TestCoordinateValidation:
    """Tests for combined coordinate validation."""
    
    def test_valid_coordinates(self):
        """Valid coordinate pairs should pass."""
        is_valid, msg = validate_coordinates(51.5074, -0.1278)
        assert is_valid
        assert msg == ""
        
        is_valid, msg = validate_coordinates(0.0, 0.0)
        assert is_valid
        assert msg == ""
    
    def test_invalid_latitude(self):
        """Invalid latitude should return error message."""
        is_valid, msg = validate_coordinates(91.0, 0.0)
        assert not is_valid
        assert "Latitude" in msg
        assert "91.0" in msg
    
    def test_invalid_longitude(self):
        """Invalid longitude should return error message."""
        is_valid, msg = validate_coordinates(0.0, 181.0)
        assert not is_valid
        assert "Longitude" in msg
        assert "181.0" in msg
    
    def test_both_invalid(self):
        """When both invalid, should report latitude first."""
        is_valid, msg = validate_coordinates(91.0, 181.0)
        assert not is_valid
        # Should report latitude error first
        assert "Latitude" in msg


class TestCoordinateEquality:
    """Tests for coordinate equality checks with precision."""
    
    def test_exactly_equal(self):
        """Exactly equal coordinates should match."""
        assert are_coordinates_equal(51.5074, -0.1278, 51.5074, -0.1278)
    
    def test_equal_within_precision(self):
        """Coordinates equal within precision should match."""
        # Default precision is 6 decimal places
        assert are_coordinates_equal(
            51.5074123, -0.1278456,
            51.5074124, -0.1278457,
            precision=6
        )
    
    def test_not_equal_beyond_precision(self):
        """Coordinates differing beyond precision should not match."""
        assert not are_coordinates_equal(
            51.5074, -0.1278,
            51.5075, -0.1278,
            precision=6
        )
    
    def test_precision_parameter(self):
        """Different precision levels should affect comparison."""
        lat1, lon1 = 51.50741, -0.12781
        lat2, lon2 = 51.50749, -0.12789
        
        # Should be equal at precision 3
        assert are_coordinates_equal(lat1, lon1, lat2, lon2, precision=3)
        
        # Should not be equal at precision 5
        assert not are_coordinates_equal(lat1, lon1, lat2, lon2, precision=5)
    
    def test_zero_coordinates(self):
        """Zero coordinates should work correctly."""
        assert are_coordinates_equal(0.0, 0.0, 0.0, 0.0)
        assert not are_coordinates_equal(0.0, 0.0, 0.1, 0.0, precision=1)
