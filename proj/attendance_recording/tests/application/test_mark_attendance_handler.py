from datetime import datetime

from attendance_recording.application.handlers import MarkAttendanceHandler
from attendance_recording.application.dto import AttendanceDTO
from attendance_recording.domain.exceptions import DuplicateAttendanceError


class FakeUseCase:
	def __init__(self, dto=None, exc=None):
		self.dto = dto
		self.exc = exc
		self.calls = []

	def execute(self, **kwargs):
		self.calls.append(kwargs)
		if self.exc:
			raise self.exc
		return self.dto


def sample_request(overrides=None):
	overrides = overrides or {}
	data = {
		"token": "abc.def.ghi",
		"scanned_student_id": "BCS/123456",
		"latitude": -1.28334,
		"longitude": 36.81667,
	}
	data.update(overrides)
	return data


def sample_dto():
	return AttendanceDTO(
		attendance_id=123,
		student_profile_id=45,
		session_id=67,
		status="present",
		is_within_radius=True,
		time_recorded=datetime(2025, 10, 25, 8, 5, 23),
		latitude=-1.28334,
		longitude=36.81667,
	)


def test_handle_success_returns_201_and_envelope():
	use_case = FakeUseCase(dto=sample_dto())
	handler = MarkAttendanceHandler(use_case)

	result = handler.handle(sample_request())

	assert result.status_code == 201
	assert result.body["success"] is True
	assert result.body["data"]["attendance_id"] == 123
	assert use_case.calls[0]["token"] == "abc.def.ghi"
	assert use_case.calls[0]["qr_code"] == "BCS/123456"


def test_handle_duplicate_returns_conflict():
	use_case = FakeUseCase(exc=DuplicateAttendanceError(1, 2))
	handler = MarkAttendanceHandler(use_case)

	result = handler.handle(sample_request())

	assert result.status_code == 409
	assert result.body["success"] is False
	assert result.body["error"]["code"] == "ALREADY_MARKED"


def test_validation_failure_short_circuits_use_case():
	use_case = FakeUseCase(dto=sample_dto())
	handler = MarkAttendanceHandler(use_case)

	result = handler.handle(sample_request({"token": None}))

	assert result.status_code == 400
	assert result.body["success"] is False
	assert result.body["error"]["code"] == "INVALID_REQUEST"
	assert use_case.calls == []
