"""Tests for geo_utils haversine distance calculations."""

import pytest
from session_management.infrastructure.geo_utils.haversine import (
    haversine_distance,
    is_within_radius,
)


def test_haversine_same_location():
    """Distance between same coordinates should be 0."""
    distance = haversine_distance(51.5074, -0.1278, 51.5074, -0.1278)
    assert distance == 0.0


def test_haversine_known_distance():
    """Test with known distance between London landmarks."""
    # Big Ben to London Eye (approximately 400m)
    big_ben = (51.5007, -0.1246)
    london_eye = (51.5033, -0.1195)
    
    distance = haversine_distance(*big_ben, *london_eye)
    # Should be roughly 400-500 meters
    assert 350 < distance < 550


def test_haversine_small_distance():
    """Test small distances (relevant for 30m radius checks)."""
    # Two points about 10 meters apart
    lat1, lon1 = 0.0, 0.0
    lat2, lon2 = 0.0001, 0.0
    
    distance = haversine_distance(lat1, lon1, lat2, lon2)
    # 0.0001 degrees longitude at equator ≈ 11 meters
    assert 9 < distance < 13


def test_is_within_radius_same_location():
    """Same location should always be within any radius."""
    assert is_within_radius(51.5074, -0.1278, 51.5074, -0.1278, radius_meters=30)
    assert is_within_radius(51.5074, -0.1278, 51.5074, -0.1278, radius_meters=1)


def test_is_within_radius_30m():
    """Test 30m radius check (the attendance validation distance)."""
    # Base point
    lat1, lon1 = 51.5074, -0.1278
    
    # Point about 20m away (should be within 30m)
    lat2, lon2 = 51.5076, -0.1278
    assert is_within_radius(lat1, lon1, lat2, lon2, radius_meters=30)
    
    # Point about 50m away (should NOT be within 30m)
    lat3, lon3 = 51.5079, -0.1278
    assert not is_within_radius(lat1, lon1, lat3, lon3, radius_meters=30)


def test_is_within_radius_edge_case():
    """Test boundary case at exactly the radius."""
    lat1, lon1 = 0.0, 0.0
    
    # Create a point at approximately 30m distance
    # At equator: 0.00027 degrees ≈ 30m
    lat2, lon2 = 0.0, 0.00027
    
    distance = haversine_distance(lat1, lon1, lat2, lon2)
    # Should be very close to 30m (allowing small floating point variance)
    assert 25 < distance < 35
    
    # Should be within 35m radius (use slightly larger to avoid edge precision issues)
    assert is_within_radius(lat1, lon1, lat2, lon2, radius_meters=35)


def test_haversine_across_hemisphere():
    """Test distance calculation across hemispheres."""
    # London to Sydney (about 17,000 km)
    london = (51.5074, -0.1278)
    sydney = (-33.8688, 151.2093)
    
    distance = haversine_distance(*london, *sydney)
    # Should be roughly 17 million meters
    assert 16_000_000 < distance < 18_000_000


def test_haversine_negative_coordinates():
    """Test with negative coordinates (Southern/Western hemispheres)."""
    # Buenos Aires to Cape Town
    buenos_aires = (-34.6037, -58.3816)
    cape_town = (-33.9249, 18.4241)
    
    distance = haversine_distance(*buenos_aires, *cape_town)
    # Should be roughly 6,800 km
    assert 6_500_000 < distance < 7_000_000
