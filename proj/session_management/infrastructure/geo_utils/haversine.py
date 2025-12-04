"""Haversine distance calculation for GPS coordinates.

Used to validate if students are within 30m radius of session location
when marking attendance.
"""

from math import radians, sin, cos, sqrt, atan2


EARTH_RADIUS_METERS = 6371000  # Mean radius of Earth in meters


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two GPS coordinates using Haversine formula.
    
    Args:
        lat1: Latitude of first point (degrees)
        lon1: Longitude of first point (degrees)
        lat2: Latitude of second point (degrees)
        lon2: Longitude of second point (degrees)
        
    Returns:
        Distance in meters between the two points
        
    Example:
        >>> haversine_distance(51.5074, -0.1278, 51.5074, -0.1279)
        76.4  # approximately 76 meters
    """
    # Convert to radians
    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    distance = EARTH_RADIUS_METERS * c
    return distance


def is_within_radius(
    lat1: float, 
    lon1: float, 
    lat2: float, 
    lon2: float, 
    radius_meters: float = 30.0
) -> bool:
    """Check if two GPS coordinates are within specified radius.
    
    Args:
        lat1: Latitude of first point (degrees)
        lon1: Longitude of first point (degrees)
        lat2: Latitude of second point (degrees)
        lon2: Longitude of second point (degrees)
        radius_meters: Maximum allowed distance in meters (default: 30)
        
    Returns:
        True if distance <= radius_meters, False otherwise
        
    Example:
        >>> is_within_radius(51.5074, -0.1278, 51.5075, -0.1278, radius_meters=30)
        True  # about 11 meters apart
    """
    distance = haversine_distance(lat1, lon1, lat2, lon2)
    return distance <= radius_meters
