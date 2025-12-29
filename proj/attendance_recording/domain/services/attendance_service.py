"""Attendance marking orchestration service."""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from ..entities.attendance import Attendance
from ..value_objects.coordinates import SessionTimeWindow
from .token_validator import TokenValidator
from .qr_validator import QRCodeValidator
from .session_validator import SessionValidator
from .location_validator import LocationValidator
from .duplicate_attendance_policy import DuplicateAttendancePolicy


class AttendanceService:
    """Orchestrates attendance marking with all validations."""
    
    def __init__(
        self,
        token_validator: TokenValidator,
        qr_validator: QRCodeValidator,
        session_validator: SessionValidator,
        location_validator: LocationValidator,
    ):
        """Initialize with validator dependencies."""
        self.token_validator = token_validator
        self.qr_validator = qr_validator
        self.session_validator = session_validator
        self.location_validator = location_validator
    
    def mark_attendance(
        self,
        token: str,
        qr_code: str,
        latitude: float,
        longitude: float,
        session_id: int,
        session_latitude: float,
        session_longitude: float,
        session_start_time: datetime,
        session_end_time: datetime,
        session_program_id: str,
        student_program_id: str,
        student_stream: Optional[str] = None,
        session_stream: Optional[str] = None,
        student_is_active: bool = True,
        expected_student_id: Optional[str] = None,
        existing_attendance: Optional[dict] = None,
    ) -> Attendance:
        """Mark attendance with complete validation chain."""
        # Step 1: Validate JWT token and extract claims
        token_payload = self.token_validator.validate_and_decode(token)
        token_student_profile_id = token_payload.get("student_profile_id")
        token_student_id = str(token_student_profile_id)
        
        # Step 2: Validate QR code format and verify it matches token
        scanned_student_id = self.qr_validator.validate_format(qr_code)

        # Prefer student_id from provider for anti-fraud; fall back to token value
        expected_student_id = expected_student_id or token_student_id
        self.qr_validator.verify_match(scanned_student_id, expected_student_id)
        
        # Step 3: Validate session is active and student is eligible
        time_window = SessionTimeWindow(
            start_time=session_start_time,
            end_time=session_end_time,
        )
        self.session_validator.validate_session_is_active(
            time_window,
            current_time=datetime.now(),
        )
        self.session_validator.validate_student_eligibility(
            student_program_id=student_program_id,
            session_program_id=session_program_id,
            student_stream=student_stream,
            session_stream=session_stream,
            student_is_active=student_is_active,
        )
        
        # Step 4: Check for duplicate attendance
        DuplicateAttendancePolicy.check_duplicate(existing_attendance)
        
        # Step 5: Validate GPS location is within radius
        student_location = (latitude, longitude)
        session_location = (session_latitude, session_longitude)
        is_within_radius = self.location_validator.check_within_radius(
            session_location,
            student_location,
        )
        
        # Step 6: Determine attendance status and create entity
        status = "present" if is_within_radius else "late"
        
        attendance = Attendance.create(
            student_id=int(token_student_profile_id),
            session_id=session_id,
            time_recorded=datetime.now(),
            latitude=latitude,
            longitude=longitude,
            status=status,
            is_within_radius=is_within_radius,
        )
        
        return attendance
