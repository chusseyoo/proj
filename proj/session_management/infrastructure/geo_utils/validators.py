"""GPS coordinate validation utilities."""

from typing import Tuple


def validate_latitude(lat: float) -> bool:
    """Validate latitude is within valid range [-90, 90].
    
    Args:
        lat: Latitude in degrees
        
    Returns:
        True if valid, False otherwise
    """
    return -90.0 <= lat <= 90.0


def validate_longitude(lon: float) -> bool:
    """Validate longitude is within valid range [-180, 180].
    
    Args:
        lon: Longitude in degrees
        
    Returns:
        True if valid, False otherwise
    """
    return -180.0 <= lon <= 180.0


def validate_coordinates(lat: float, lon: float) -> Tuple[bool, str]:
    """Validate both latitude and longitude.
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> validate_coordinates(51.5074, -0.1278)
        (True, '')
        >>> validate_coordinates(91.0, -0.1278)
        (False, 'Latitude must be between -90 and 90')
    """
    if not validate_latitude(lat):
        return False, f"Latitude must be between -90 and 90, got {lat}"
    
    if not validate_longitude(lon):
        return False, f"Longitude must be between -180 and 180, got {lon}"
    
    return True, ""


def are_coordinates_equal(
    lat1: float, 
    lon1: float, 
    lat2: float, 
    lon2: float, 
    precision: int = 6
) -> bool:
    """Check if two coordinate pairs are equal within specified decimal precision.
    
    Args:
        lat1, lon1: First coordinate pair
        lat2, lon2: Second coordinate pair
        precision: Number of decimal places for comparison (default: 6 ≈ 0.11m)
        
    Returns:
        True if coordinates are equal within precision
    """
    return (
        round(lat1, precision) == round(lat2, precision) and
        round(lon1, precision) == round(lon2, precision)
    )
