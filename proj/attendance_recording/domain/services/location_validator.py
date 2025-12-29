"""Location validation service using Haversine formula."""
from math import radians, cos, sin, asin, sqrt
from typing import Tuple

from ..exceptions import (
    InvalidCoordinatesError,
    OutsideRadiusWarning,
)
from ..value_objects import GPSCoordinate


class LocationValidator:
    """Validates student location against session location using Haversine formula.
    
    Haversine formula calculates great-circle distance between two GPS coordinates.
    """
    
    # Earth radius in meters
    EARTH_RADIUS_METERS = 6371000
    
    # Allowed radius in meters (30 meters)
    ALLOWED_RADIUS_METERS = 30
    
    @staticmethod
    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two GPS coordinates using Haversine formula.
        
        Args:
            lat1, lon1: First coordinate (session location)
            lat2, lon2: Second coordinate (student location)
        
        Returns:
            Distance in meters
        """
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        
        # Distance in meters
        distance = LocationValidator.EARTH_RADIUS_METERS * c
        return distance
    
    @classmethod
    def validate_coordinates(cls, latitude: float, longitude: float) -> GPSCoordinate:
        """Validate GPS coordinates format and range.
        
        Args:
            latitude: Latitude value
            longitude: Longitude value
        
        Returns:
            GPSCoordinate value object
        
        Raises:
            InvalidCoordinatesError: If coordinates are invalid
        """
        try:
            return GPSCoordinate(latitude, longitude)
        except ValueError as e:
            raise InvalidCoordinatesError(str(e))
    
    @classmethod
    def check_within_radius(
        cls,
        session_location: Tuple[float, float],
        student_location: Tuple[float, float],
    ) -> bool:
        """Check if student location is within allowed radius of session location.
        
        Args:
            session_location: Tuple of (latitude, longitude) for session
            student_location: Tuple of (latitude, longitude) for student
        
        Returns:
            True if within radius, False otherwise
        """
        session_lat, session_lon = session_location
        student_lat, student_lon = student_location
        
        distance = cls.haversine(session_lat, session_lon, student_lat, student_lon)
        
        return distance <= cls.ALLOWED_RADIUS_METERS
    
    @classmethod
    def get_distance(
        cls,
        session_location: Tuple[float, float],
        student_location: Tuple[float, float],
    ) -> float:
        """Get distance in meters between session and student location.
        
        Args:
            session_location: Tuple of (latitude, longitude) for session
            student_location: Tuple of (latitude, longitude) for student
        
        Returns:
            Distance in meters
        """
        session_lat, session_lon = session_location
        student_lat, student_lon = student_location
        
        return cls.haversine(session_lat, session_lon, student_lat, student_lon)
