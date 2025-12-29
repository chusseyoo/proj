"""DRF serializers for attendance recording API endpoints."""
from rest_framework import serializers
import re


class MarkAttendanceRequestSerializer(serializers.Serializer):
    """Request serializer for POST /api/v1/attendance/mark endpoint.
    
    Validates:
    - token: JWT format string
    - scanned_student_id: QR code format (ABC/123456)
    - latitude: Decimal -90 to 90 with 8 decimal places
    - longitude: Decimal -180 to 180 with 8 decimal places
    """
    
    token = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="JWT token from email link"
    )
    
    scanned_student_id = serializers.RegexField(
        regex=r'^[A-Z]{3}/[0-9]{6}$',
        required=True,
        error_messages={
            'invalid': 'Invalid QR code format. Please scan your student ID card.',
            'required': 'QR code is required',
        },
        help_text="Student ID in format ABC/123456"
    )
    
    latitude = serializers.DecimalField(
        max_digits=10,
        decimal_places=8,
        required=True,
        min_value=-90,
        max_value=90,
        error_messages={
            'required': 'Latitude is required',
            'invalid': 'Invalid GPS coordinates. Please enable location services.',
            'min_value': 'Latitude must be between -90 and 90',
            'max_value': 'Latitude must be between -90 and 90',
        },
        help_text="Latitude coordinate (-90 to 90)"
    )
    
    longitude = serializers.DecimalField(
        max_digits=11,
        decimal_places=8,
        required=True,
        min_value=-180,
        max_value=180,
        error_messages={
            'required': 'Longitude is required',
            'invalid': 'Invalid GPS coordinates. Please enable location services.',
            'min_value': 'Longitude must be between -180 and 180',
            'max_value': 'Longitude must be between -180 and 180',
        },
        help_text="Longitude coordinate (-180 to 180)"
    )
    
    def validate(self, attrs):
        """Additional validation: reject (0, 0) coordinates."""
        lat = float(attrs.get('latitude', 0))
        lon = float(attrs.get('longitude', 0))
        
        if lat == 0.0 and lon == 0.0:
            raise serializers.ValidationError({
                'coordinates': 'Invalid GPS coordinates. Please enable location services.'
            })
        
        return attrs


class AttendanceResponseSerializer(serializers.Serializer):
    """Response serializer for successful attendance creation.
    
    Returns:
    - attendance_id: Primary key of created record
    - student_profile_id: Student who marked attendance
    - session_id: Session for which attendance was marked
    - status: 'present' or 'late'
    - is_within_radius: Whether student was within 30m radius
    - time_recorded: UTC timestamp of record creation
    - latitude: Student's GPS latitude
    - longitude: Student's GPS longitude
    """
    
    attendance_id = serializers.IntegerField(read_only=True)
    student_profile_id = serializers.IntegerField(read_only=True)
    session_id = serializers.IntegerField(read_only=True)
    status = serializers.ChoiceField(choices=['present', 'late'], read_only=True)
    is_within_radius = serializers.BooleanField(read_only=True)
    time_recorded = serializers.DateTimeField(read_only=True, format='iso-8601')
    latitude = serializers.DecimalField(
        max_digits=10,
        decimal_places=8,
        read_only=True
    )
    longitude = serializers.DecimalField(
        max_digits=11,
        decimal_places=8,
        read_only=True
    )
