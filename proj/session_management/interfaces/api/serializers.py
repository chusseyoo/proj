"""REST API serializers for Session Management."""

from rest_framework import serializers
from datetime import datetime, timedelta


class CreateSessionRequestSerializer(serializers.Serializer):
    """Serializer for creating a session."""
    program_id = serializers.IntegerField(required=True, min_value=1)
    course_id = serializers.IntegerField(required=True, min_value=1)
    stream_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    time_created = serializers.DateTimeField(required=True)
    time_ended = serializers.DateTimeField(required=True)
    latitude = serializers.DecimalField(
        required=True,
        max_digits=10,
        decimal_places=8,
        min_value=-90,
        max_value=90
    )
    longitude = serializers.DecimalField(
        required=True,
        max_digits=11,
        decimal_places=8,
        min_value=-180,
        max_value=180
    )
    location_description = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=200
    )

    def validate(self, data):
        """Validate time window."""
        time_created = data.get('time_created')
        time_ended = data.get('time_ended')
        
        if time_created and time_ended:
            if time_ended <= time_created:
                raise serializers.ValidationError({
                    "time_ended": "End time must be after start time"
                })
            
            duration = time_ended - time_created
            min_duration = timedelta(minutes=10)
            max_duration = timedelta(hours=24)
            
            if duration < min_duration:
                raise serializers.ValidationError({
                    "time_window": "Session duration must be at least 10 minutes"
                })
            
            if duration > max_duration:
                raise serializers.ValidationError({
                    "time_window": "Session duration cannot exceed 24 hours"
                })
        
        return data


class SessionResponseSerializer(serializers.Serializer):
    """Serializer for session response."""
    session_id = serializers.IntegerField()
    program_id = serializers.IntegerField()
    course_id = serializers.IntegerField()
    lecturer_id = serializers.IntegerField()
    stream_id = serializers.IntegerField(allow_null=True)
    time_created = serializers.DateTimeField()
    time_ended = serializers.DateTimeField()
    latitude = serializers.CharField()
    longitude = serializers.CharField()
    location_description = serializers.CharField(allow_null=True)
    status = serializers.CharField()


class PaginatedSessionResponseSerializer(serializers.Serializer):
    """Serializer for paginated session list response."""
    results = SessionResponseSerializer(many=True)
    total_count = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    has_next = serializers.BooleanField()
    has_previous = serializers.BooleanField()


class SessionFilterSerializer(serializers.Serializer):
    """Serializer for session list filters."""
    course_id = serializers.IntegerField(required=False, min_value=1)
    program_id = serializers.IntegerField(required=False, min_value=1)
    stream_id = serializers.IntegerField(required=False, min_value=1)
    from_time = serializers.DateTimeField(required=False)
    to_time = serializers.DateTimeField(required=False)
    status = serializers.ChoiceField(
        choices=['active', 'ended', 'created'],
        required=False
    )
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)
