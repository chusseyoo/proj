"""Tests for attendance recording API interface layer.

Tests the DRF views and serializers for:
- Request validation
- Response formatting
- Error handling
- HTTP status codes
- API envelope structure
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from django.test import RequestFactory
from rest_framework.test import APITestCase, APIClient
from django.utils import timezone

from attendance_recording.interfaces.api.views import MarkAttendanceView
from attendance_recording.interfaces.api.serializers import (
    MarkAttendanceRequestSerializer,
    AttendanceResponseSerializer,
)
from attendance_recording.application.dto import AttendanceDTO
from attendance_recording.application.handlers import MarkAttendanceResult


@pytest.mark.django_db
class TestMarkAttendanceRequestSerializer:
    """Test request serializer validation."""
    
    def test_valid_request_data(self):
        """Valid request passes all validations."""
        data = {
            'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature',
            'scanned_student_id': 'BCS/234344',
            'latitude': '-1.28334000',
            'longitude': '36.81667000',
        }
        
        serializer = MarkAttendanceRequestSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['token'] == data['token']
        assert serializer.validated_data['scanned_student_id'] == 'BCS/234344'
        assert serializer.validated_data['latitude'] == Decimal('-1.28334000')
        assert serializer.validated_data['longitude'] == Decimal('36.81667000')
    
    def test_missing_token_field(self):
        """Missing token field returns validation error."""
        data = {
            'scanned_student_id': 'BCS/234344',
            'latitude': '-1.28334000',
            'longitude': '36.81667000',
        }
        
        serializer = MarkAttendanceRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'token' in serializer.errors
    
    def test_missing_scanned_student_id(self):
        """Missing QR code returns validation error."""
        data = {
            'token': 'eyJhbGc.test.sig',
            'latitude': '-1.28334000',
            'longitude': '36.81667000',
        }
        
        serializer = MarkAttendanceRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'scanned_student_id' in serializer.errors
    
    def test_invalid_qr_format_lowercase(self):
        """QR code must be uppercase."""
        data = {
            'token': 'eyJhbGc.test.sig',
            'scanned_student_id': 'bcs/234344',
            'latitude': '-1.28334000',
            'longitude': '36.81667000',
        }
        
        serializer = MarkAttendanceRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'scanned_student_id' in serializer.errors
    
    def test_invalid_qr_format_wrong_pattern(self):
        """QR code must match ABC/123456 pattern."""
        data = {
            'token': 'eyJhbGc.test.sig',
            'scanned_student_id': 'BC/234344',  # Only 2 letters
            'latitude': '-1.28334000',
            'longitude': '36.81667000',
        }
        
        serializer = MarkAttendanceRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'scanned_student_id' in serializer.errors
    
    def test_missing_latitude(self):
        """Missing latitude returns error."""
        data = {
            'token': 'eyJhbGc.test.sig',
            'scanned_student_id': 'BCS/234344',
            'longitude': '36.81667000',
        }
        
        serializer = MarkAttendanceRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'latitude' in serializer.errors
    
    def test_missing_longitude(self):
        """Missing longitude returns error."""
        data = {
            'token': 'eyJhbGc.test.sig',
            'scanned_student_id': 'BCS/234344',
            'latitude': '-1.28334000',
        }
        
        serializer = MarkAttendanceRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'longitude' in serializer.errors
    
    def test_latitude_out_of_range_negative(self):
        """Latitude must be >= -90."""
        data = {
            'token': 'eyJhbGc.test.sig',
            'scanned_student_id': 'BCS/234344',
            'latitude': '-91.0',
            'longitude': '36.81667000',
        }
        
        serializer = MarkAttendanceRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'latitude' in serializer.errors
    
    def test_latitude_out_of_range_positive(self):
        """Latitude must be <= 90."""
        data = {
            'token': 'eyJhbGc.test.sig',
            'scanned_student_id': 'BCS/234344',
            'latitude': '91.0',
            'longitude': '36.81667000',
        }
        
        serializer = MarkAttendanceRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'latitude' in serializer.errors
    
    def test_longitude_out_of_range_negative(self):
        """Longitude must be >= -180."""
        data = {
            'token': 'eyJhbGc.test.sig',
            'scanned_student_id': 'BCS/234344',
            'latitude': '-1.28334000',
            'longitude': '-181.0',
        }
        
        serializer = MarkAttendanceRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'longitude' in serializer.errors
    
    def test_longitude_out_of_range_positive(self):
        """Longitude must be <= 180."""
        data = {
            'token': 'eyJhbGc.test.sig',
            'scanned_student_id': 'BCS/234344',
            'latitude': '-1.28334000',
            'longitude': '181.0',
        }
        
        serializer = MarkAttendanceRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'longitude' in serializer.errors
    
    def test_zero_coordinates_not_allowed(self):
        """Coordinates (0, 0) are rejected."""
        data = {
            'token': 'eyJhbGc.test.sig',
            'scanned_student_id': 'BCS/234344',
            'latitude': '0.0',
            'longitude': '0.0',
        }
        
        serializer = MarkAttendanceRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'coordinates' in serializer.errors


@pytest.mark.django_db
class TestAttendanceResponseSerializer:
    """Test response serializer structure."""
    
    def test_serialize_dto_to_response(self):
        """Serialize AttendanceDTO to API response format."""
        dto = AttendanceDTO(
            attendance_id=501,
            student_profile_id=123,
            session_id=456,
            status='present',
            is_within_radius=True,
            time_recorded=datetime(2025, 10, 25, 8, 5, 23),
            latitude=-1.28334,
            longitude=36.81667,
        )
        
        serializer = AttendanceResponseSerializer(dto)
        data = serializer.data
        
        assert data['attendance_id'] == 501
        assert data['student_profile_id'] == 123
        assert data['session_id'] == 456
        assert data['status'] == 'present'
        assert data['is_within_radius'] is True
        assert 'time_recorded' in data
        assert float(data['latitude']) == pytest.approx(-1.28334)
        assert float(data['longitude']) == pytest.approx(36.81667)


@pytest.mark.django_db
class TestMarkAttendanceViewIntegration:
    """Integration tests for the API view with mocked handler."""
    
    def setup_method(self):
        """Set up test client and factory."""
        self.client = APIClient()
        self.factory = RequestFactory()
        self.url = '/api/v1/attendance/mark'
    
    @patch('attendance_recording.interfaces.api.views.MarkAttendanceHandler')
    def test_successful_attendance_creation(self, mock_handler_class):
        """Valid request returns 201 Created with attendance data."""
        # Mock handler to return success result
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        
        mock_result = MarkAttendanceResult(
            status_code=201,
            body={
                'success': True,
                'data': {
                    'attendance_id': 501,
                    'student_profile_id': 123,
                    'session_id': 456,
                    'status': 'present',
                    'is_within_radius': True,
                    'time_recorded': '2025-10-25T08:05:23.456Z',
                    'latitude': -1.28334,
                    'longitude': 36.81667,
                },
                'message': 'Attendance marked successfully',
            }
        )
        mock_handler.handle.return_value = mock_result
        
        request_data = {
            'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature',
            'scanned_student_id': 'BCS/234344',
            'latitude': '-1.28334000',
            'longitude': '36.81667000',
        }
        
        response = self.client.post(
            self.url,
            data=request_data,
            format='json'
        )
        
        assert response.status_code == 201
        assert response.data['success'] is True
        assert response.data['data']['attendance_id'] == 501
        assert response.data['message'] == 'Attendance marked successfully'
    
    def test_invalid_request_missing_token(self):
        """Missing token field returns 400 Bad Request."""
        request_data = {
            'scanned_student_id': 'BCS/234344',
            'latitude': '-1.28334000',
            'longitude': '36.81667000',
        }
        
        response = self.client.post(
            self.url,
            data=request_data,
            format='json'
        )
        
        assert response.status_code == 400
        assert response.data['success'] is False
        assert response.data['error']['code'] == 'INVALID_REQUEST'
        assert 'token' in response.data['error']['details']
    
    def test_invalid_qr_code_format(self):
        """Invalid QR code format returns 400 with specific error."""
        request_data = {
            'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.sig',
            'scanned_student_id': 'bcs/234344',  # lowercase
            'latitude': '-1.28334000',
            'longitude': '36.81667000',
        }
        
        response = self.client.post(
            self.url,
            data=request_data,
            format='json'
        )
        
        assert response.status_code == 400
        assert response.data['success'] is False
        assert 'scanned_student_id' in response.data['error']['details']
    
    def test_coordinates_out_of_range(self):
        """Out of range coordinates return 400."""
        request_data = {
            'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.sig',
            'scanned_student_id': 'BCS/234344',
            'latitude': '91.0',  # > 90
            'longitude': '36.81667000',
        }
        
        response = self.client.post(
            self.url,
            data=request_data,
            format='json'
        )
        
        assert response.status_code == 400
        assert response.data['success'] is False
        assert 'latitude' in response.data['error']['details']
    
    def test_zero_zero_coordinates_rejected(self):
        """Coordinates (0, 0) are rejected."""
        request_data = {
            'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.sig',
            'scanned_student_id': 'BCS/234344',
            'latitude': '0.0',
            'longitude': '0.0',
        }
        
        response = self.client.post(
            self.url,
            data=request_data,
            format='json'
        )
        
        assert response.status_code == 400
        assert response.data['success'] is False
        assert 'coordinates' in response.data['error']['details']
    
    @patch('attendance_recording.interfaces.api.views.MarkAttendanceHandler')
    def test_duplicate_attendance_returns_409(self, mock_handler_class):
        """Duplicate attendance attempt returns 409 Conflict."""
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        
        mock_result = MarkAttendanceResult(
            status_code=409,
            body={
                'success': False,
                'error': {
                    'code': 'ALREADY_MARKED',
                    'message': 'You have already marked attendance for this session.',
                    'details': {
                        'existing_attendance_id': 500,
                        'time_recorded': '2025-10-25T08:03:15.123Z',
                    }
                }
            }
        )
        mock_handler.handle.return_value = mock_result
        
        request_data = {
            'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature',
            'scanned_student_id': 'BCS/234344',
            'latitude': '-1.28334000',
            'longitude': '36.81667000',
        }
        
        response = self.client.post(
            self.url,
            data=request_data,
            format='json'
        )
        
        assert response.status_code == 409
        assert response.data['success'] is False
        assert response.data['error']['code'] == 'ALREADY_MARKED'
    
    @patch('attendance_recording.interfaces.api.views.MarkAttendanceHandler')
    def test_qr_mismatch_returns_403(self, mock_handler_class):
        """QR code mismatch returns 403 Forbidden."""
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        
        mock_result = MarkAttendanceResult(
            status_code=403,
            body={
                'success': False,
                'error': {
                    'code': 'QR_CODE_MISMATCH',
                    'message': 'This QR code does not match your attendance link.',
                    'details': {
                        'scanned_student_id': 'MIT/123456',
                        'expected_student_id': 'BCS/234344'
                    }
                }
            }
        )
        mock_handler.handle.return_value = mock_result
        
        request_data = {
            'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature',
            'scanned_student_id': 'MIT/123456',
            'latitude': '-1.28334000',
            'longitude': '36.81667000',
        }
        
        response = self.client.post(
            self.url,
            data=request_data,
            format='json'
        )
        
        assert response.status_code == 403
        assert response.data['success'] is False
        assert response.data['error']['code'] == 'QR_CODE_MISMATCH'
    
    def test_empty_request_body(self):
        """Empty request body returns 400."""
        response = self.client.post(
            self.url,
            data={},
            format='json'
        )
        
        assert response.status_code == 400
        assert response.data['success'] is False
        assert response.data['error']['code'] == 'INVALID_REQUEST'
    
    def test_only_post_method_allowed(self):
        """Only POST method is allowed."""
        # GET should not be allowed
        response = self.client.get(self.url)
        assert response.status_code == 405
        
        # PUT should not be allowed
        response = self.client.put(self.url, data={}, format='json')
        assert response.status_code == 405
        
        # DELETE should not be allowed
        response = self.client.delete(self.url)
        assert response.status_code == 405
