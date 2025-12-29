"""Django REST Framework views for attendance recording API."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from attendance_recording.interfaces.api.serializers import (
    MarkAttendanceRequestSerializer,
    AttendanceResponseSerializer,
)
from attendance_recording.application.handlers import MarkAttendanceHandler
from attendance_recording.application.use_cases import MarkAttendanceUseCase
from attendance_recording.infrastructure.repositories.attendance_repository import (
    AttendanceRepositoryImpl,
)
from attendance_recording.infrastructure.persistence.session_provider import get_session_info
from attendance_recording.infrastructure.persistence.student_provider import get_student_info
from attendance_recording.domain.services.attendance_service import AttendanceService
from attendance_recording.domain.services.token_validator import TokenValidator
from attendance_recording.domain.services.qr_validator import QRCodeValidator
from attendance_recording.domain.services.session_validator import SessionValidator
from attendance_recording.domain.services.location_validator import LocationValidator


class MarkAttendanceView(APIView):
    """POST /api/v1/attendance/mark - Mark attendance with token-based auth.
    
    Authentication: Token in request body (not Authorization header)
    
    Request Body:
        {
            "token": "eyJhbGc...",
            "scanned_student_id": "BCS/234344",
            "latitude": "-1.28334000",
            "longitude": "36.81667000"
        }
    
    Success Response (201 Created):
        {
            "success": true,
            "data": {
                "attendance_id": 501,
                "student_profile_id": 123,
                "session_id": 456,
                "status": "present",
                "is_within_radius": true,
                "time_recorded": "2025-10-25T08:05:23.456Z",
                "latitude": "-1.28334000",
                "longitude": "36.81667000"
            },
            "message": "Attendance marked successfully"
        }
    
    Error Responses:
        - 400: Invalid request (validation errors)
        - 403: Forbidden (QR mismatch, inactive student, program mismatch)
        - 404: Not found (session/student doesn't exist)
        - 409: Conflict (duplicate attendance)
        - 410: Gone (token expired, session ended)
        - 425: Too early (session not started)
        - 500: Internal server error
    """
    
    # Allow unauthenticated access (token-based, not session-based)
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        """Handle POST request to mark attendance."""
        # Step 1: Validate request format using DRF serializer
        request_serializer = MarkAttendanceRequestSerializer(data=request.data)
        
        if not request_serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "All fields are required",
                        "details": request_serializer.errors,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = request_serializer.validated_data
        
        # Step 2: Build application layer dependencies
        attendance_repository = AttendanceRepositoryImpl()
        jwt_secret = getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY)
        token_validator = TokenValidator(secret_key=jwt_secret)
        attendance_service = AttendanceService(
            token_validator=token_validator,
            qr_validator=QRCodeValidator(),
            session_validator=SessionValidator(),
            location_validator=LocationValidator(),
        )
        
        use_case = MarkAttendanceUseCase(
            attendance_service=attendance_service,
            token_validator=token_validator,
            attendance_repository=attendance_repository,
            session_provider=get_session_info,
            student_provider=get_student_info,
        )
        
        # Step 3: Invoke handler
        handler = MarkAttendanceHandler(use_case)
        result = handler.handle({
            'token': validated_data['token'],
            'scanned_student_id': validated_data['scanned_student_id'],
            'latitude': float(validated_data['latitude']),
            'longitude': float(validated_data['longitude']),
        })
        
        # Step 4: Return handler response
        return Response(result.body, status=result.status_code)
