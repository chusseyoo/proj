"""Application use case: Mark attendance with three-factor verification."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Any, Protocol

from attendance_recording.domain.services.attendance_service import AttendanceService
from attendance_recording.domain.services.token_validator import TokenValidator
from attendance_recording.domain.exceptions import (
	DuplicateAttendanceError,
	InvalidTokenError,
	StudentNotEligibleError,
)
from attendance_recording.application.dto import AttendanceDTO
from attendance_recording.domain.entities.attendance import Attendance
from attendance_recording.application.exceptions import ResourceNotFoundError


class AttendanceRepository(Protocol):
    """Repository interface for attendance persistence."""

    def exists_for_student_and_session(self, student_profile_id: int, session_id: int) -> bool:
        ...

    def create(self, attendance: Attendance) -> Attendance:
        ...


@dataclass
class MarkAttendanceUseCase:
    """Orchestrates attendance marking and persistence."""

    attendance_service: AttendanceService
    token_validator: TokenValidator
    attendance_repository: AttendanceRepository
    session_provider: Callable[[int], Dict[str, Any]]
    student_provider: Callable[[int], Dict[str, Any]]

    def execute(self, *, token: str, qr_code: str, latitude: float, longitude: float) -> AttendanceDTO:
        """Run full workflow: decode token, validate, persist, return DTO."""
        # Decode token to obtain identifiers (validates signature/claims)
        payload = self.token_validator.validate_and_decode(token)
        student_profile_id = payload.get("student_profile_id")
        session_id = payload.get("session_id")

        if student_profile_id is None or session_id is None:
            raise InvalidTokenError("Token must contain student_profile_id and session_id")

        # Duplicate check before any heavy work
        if self.attendance_repository.exists_for_student_and_session(student_profile_id, session_id):
            raise DuplicateAttendanceError(
                f"Attendance already exists for student {student_profile_id} in session {session_id}"
            )

        # Fetch session and student details from providers
        session = self.session_provider(session_id)
        if not session:
            raise ResourceNotFoundError(f"Session {session_id} not found")

        required_session_fields = [
            "latitude",
            "longitude",
            "start_time",
            "end_time",
            "program_id",
        ]
        missing_session_fields = [field for field in required_session_fields if field not in session]
        if missing_session_fields:
            raise ResourceNotFoundError(
                f"Session {session_id} missing fields: {', '.join(missing_session_fields)}"
            )

        student = self.student_provider(student_profile_id)
        if not student:
            raise ResourceNotFoundError(f"Student profile {student_profile_id} not found")

        # Basic consistency between token claim and provider response
        provider_student_id = student.get("student_profile_id") or student.get("id")
        if provider_student_id is not None and int(provider_student_id) != int(student_profile_id):
            raise StudentNotEligibleError(
                reason="Token student does not match retrieved student profile"
            )

        student_is_active = bool(student.get("is_active", True))
        student_program_id = student.get("program_id")
        student_stream = student.get("stream_id")
        student_id_code = student.get("student_id")
        if not student_id_code:
            raise ResourceNotFoundError(
                f"Student profile {student_profile_id} missing student_id for QR verification"
            )

        # Call domain service for full validation + entity creation
        attendance = self.attendance_service.mark_attendance(
            token=token,
            qr_code=qr_code,
            latitude=latitude,
            longitude=longitude,
            session_id=session_id,
            session_latitude=session["latitude"],
            session_longitude=session["longitude"],
            session_start_time=session["start_time"],
            session_end_time=session["end_time"],
            session_program_id=session.get("program_id"),
            student_program_id=student_program_id,
            student_stream=student_stream,
            session_stream=session.get("stream_id"),
            student_is_active=student_is_active,
            expected_student_id=student_id_code,
        )

        # Persist via repository (could assign ID)
        saved = self.attendance_repository.create(attendance)

        return AttendanceDTO.from_entity(saved)
