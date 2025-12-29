"""Handler for the mark attendance application use case."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from attendance_recording.application.use_cases import MarkAttendanceUseCase
from attendance_recording.application.serializers import (
	MarkAttendanceRequestSerializer,
	AttendanceResponseSerializer,
)
from attendance_recording.application.exceptions import (
	RequestValidationError,
	ResourceNotFoundError,
)
from attendance_recording.domain.exceptions import (
	AttendanceRecordingException,
	DuplicateAttendanceError,
	InvalidCoordinatesError,
	InvalidTokenError,
	QRMismatchError,
	SessionNotActiveError,
	StudentNotEligibleError,
	TokenExpiredError,
)


@dataclass
class MarkAttendanceResult:
	"""Handler response with HTTP semantics."""

	status_code: int
	body: Dict[str, Any]


class MarkAttendanceHandler:
	"""Validate request, invoke use case, and map exceptions to responses."""

	def __init__(self, use_case: MarkAttendanceUseCase):
		self.use_case = use_case
		self._request_serializer = MarkAttendanceRequestSerializer()

	def handle(self, request_data: Dict[str, Any]) -> MarkAttendanceResult:
		try:
			command = self._request_serializer.validate(request_data)
			dto = self.use_case.execute(
				token=command.token,
				qr_code=command.scanned_student_id,
				latitude=command.latitude,
				longitude=command.longitude,
			)
			return MarkAttendanceResult(
				status_code=201,
				body=self._success_body(dto),
			)
		except Exception as exc:  # noqa: BLE001
			status_code, body = self._handle_exception(exc)
			return MarkAttendanceResult(status_code=status_code, body=body)

	def _success_body(self, dto) -> Dict[str, Any]:
		return {
			"success": True,
			"data": AttendanceResponseSerializer.serialize(dto),
			"message": "Attendance marked successfully",
		}

	def _handle_exception(self, exc: Exception) -> Tuple[int, Dict[str, Any]]:
		code = "UNEXPECTED_ERROR"
		status = 500
		details: Dict[str, Any] | None = None

		if isinstance(exc, RequestValidationError):
			code = "INVALID_REQUEST"
			status = 400
			details = exc.details
		elif isinstance(exc, InvalidTokenError):
			code = "INVALID_TOKEN"
			status = 400
		elif isinstance(exc, TokenExpiredError):
			code = "TOKEN_EXPIRED"
			status = 410
		elif isinstance(exc, QRMismatchError):
			code = "QR_CODE_MISMATCH"
			status = 403
		elif isinstance(exc, StudentNotEligibleError):
			code = "NOT_ELIGIBLE"
			status = 403
		elif isinstance(exc, SessionNotActiveError):
			code = "SESSION_NOT_ACTIVE"
			status = 400
		elif isinstance(exc, InvalidCoordinatesError):
			code = "INVALID_COORDINATES"
			status = 400
		elif isinstance(exc, ResourceNotFoundError):
			code = "NOT_FOUND"
			status = 404
		elif isinstance(exc, DuplicateAttendanceError):
			code = "ALREADY_MARKED"
			status = 409
		elif isinstance(exc, AttendanceRecordingException):
			code = "DOMAIN_ERROR"
			status = 400

		message = str(exc) if str(exc) else "Request could not be processed"
		return status, {
			"success": False,
			"error": {
				"code": code,
				"message": message,
				"details": details or {},
			},
		}
