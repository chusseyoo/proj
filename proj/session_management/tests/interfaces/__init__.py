"""Basic tests for Session Management API serializers."""

import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from session_management.interfaces.api.serializers import (
    CreateSessionRequestSerializer,
    SessionResponseSerializer,
    SessionFilterSerializer,
)


class TestCreateSessionRequestSerializer:
    """Tests for CreateSessionRequestSerializer."""
    
    def test_valid_data(self):
        """Should validate correct session data."""
        now = timezone.now()
        data = {
            'program_id': 1,
            'course_id': 1,
            'stream_id': None,
            'time_created': now.isoformat(),
            'time_ended': (now + timedelta(hours=1)).isoformat(),
            'latitude': '51.5074',
            'longitude': '-0.1278',
            'location_description': 'Main Hall'
        }
        
        serializer = CreateSessionRequestSerializer(data=data)
        assert serializer.is_valid()
    
    def test_invalid_time_window(self):
        """Should reject time_ended before time_created."""
        now = timezone.now()
        data = {
            'program_id': 1,
            'course_id': 1,
            'time_created': now.isoformat(),
            'time_ended': (now - timedelta(hours=1)).isoformat(),
            'latitude': '51.5074',
            'longitude': '-0.1278',
        }
        
        serializer = CreateSessionRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'time_ended' in serializer.errors or 'time_window' in serializer.errors
    
    def test_duration_too_short(self):
        """Should reject session duration less than 10 minutes."""
        now = timezone.now()
        data = {
            'program_id': 1,
            'course_id': 1,
            'time_created': now.isoformat(),
            'time_ended': (now + timedelta(minutes=5)).isoformat(),
            'latitude': '51.5074',
            'longitude': '-0.1278',
        }
        
        serializer = CreateSessionRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'time_window' in serializer.errors
    
    def test_invalid_latitude(self):
        """Should reject latitude outside [-90, 90]."""
        now = timezone.now()
        data = {
            'program_id': 1,
            'course_id': 1,
            'time_created': now.isoformat(),
            'time_ended': (now + timedelta(hours=1)).isoformat(),
            'latitude': '95.0',  # Invalid
            'longitude': '-0.1278',
        }
        
        serializer = CreateSessionRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'latitude' in serializer.errors
    
    def test_invalid_longitude(self):
        """Should reject longitude outside [-180, 180]."""
        now = timezone.now()
        data = {
            'program_id': 1,
            'course_id': 1,
            'time_created': now.isoformat(),
            'time_ended': (now + timedelta(hours=1)).isoformat(),
            'latitude': '51.5074',
            'longitude': '200.0',  # Invalid
        }
        
        serializer = CreateSessionRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'longitude' in serializer.errors


class TestSessionFilterSerializer:
    """Tests for SessionFilterSerializer."""
    
    def test_valid_filters(self):
        """Should validate correct filter parameters."""
        data = {
            'course_id': 1,
            'program_id': 1,
            'page': 2,
            'page_size': 10,
        }
        
        serializer = SessionFilterSerializer(data=data)
        assert serializer.is_valid()
    
    def test_page_defaults(self):
        """Should use default values for page and page_size."""
        data = {}
        
        serializer = SessionFilterSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['page'] == 1
        assert serializer.validated_data['page_size'] == 20
    
    def test_page_size_max_limit(self):
        """Should reject page_size over 100."""
        data = {'page_size': 150}
        
        serializer = SessionFilterSerializer(data=data)
        assert not serializer.is_valid()
        assert 'page_size' in serializer.errors
