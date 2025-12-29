"""Request and response serializers for attendance recording application layer."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict

from attendance_recording.application.dto import AttendanceDTO
from attendance_recording.application.exceptions import RequestValidationError


@dataclass
class MarkAttendanceCommand:
	"""Validated request payload for mark attendance."""

	token: str
	scanned_student_id: str
	latitude: float
	longitude: float


class MarkAttendanceRequestSerializer:
	"""Validate incoming request data before invoking the use case."""

	QR_PATTERN = re.compile(r"^[A-Z]{3}/[0-9]{6}$")

	def validate(self, data: Dict[str, Any]) -> MarkAttendanceCommand:
		if not isinstance(data, dict):
			raise RequestValidationError("Request payload must be a JSON object")

		errors: Dict[str, str] = {}

		token = data.get("token")
		if not token or not isinstance(token, str):
			errors["token"] = "Token is required"

		scanned_student_id = data.get("scanned_student_id")
		if not scanned_student_id or not isinstance(scanned_student_id, str):
			errors["scanned_student_id"] = "scanned_student_id is required"
		elif not self.QR_PATTERN.match(scanned_student_id):
			errors["scanned_student_id"] = "Invalid QR code format. Expected ABC/123456"

		latitude_raw = data.get("latitude")
		longitude_raw = data.get("longitude")

		try:
			latitude = float(latitude_raw)
		except (TypeError, ValueError):
			errors["latitude"] = "Latitude must be a number"
			latitude = None  # type: ignore

		try:
			longitude = float(longitude_raw)
		except (TypeError, ValueError):
			errors["longitude"] = "Longitude must be a number"
			longitude = None  # type: ignore

		if latitude is not None and not (-90 <= latitude <= 90):
			errors["latitude"] = "Latitude must be between -90 and 90"

		if longitude is not None and not (-180 <= longitude <= 180):
			errors["longitude"] = "Longitude must be between -180 and 180"

		if latitude is not None and longitude is not None:
			if latitude == 0 and longitude == 0:
				errors["coordinates"] = "Coordinates (0,0) are not allowed"

		if errors:
			raise RequestValidationError("Invalid request payload", details=errors)

		return MarkAttendanceCommand(
			token=token,
			scanned_student_id=scanned_student_id,
			latitude=latitude,
			longitude=longitude,
		)


class AttendanceResponseSerializer:
	"""Serialize AttendanceDTO to API response shape."""

	@staticmethod
	def serialize(dto: AttendanceDTO) -> Dict[str, Any]:
		return {
			"attendance_id": dto.attendance_id,
			"student_profile_id": dto.student_profile_id,
			"session_id": dto.session_id,
			"status": dto.status,
			"is_within_radius": dto.is_within_radius,
			"time_recorded": dto.time_recorded.isoformat(),
			"latitude": dto.latitude,
			"longitude": dto.longitude,
		}
