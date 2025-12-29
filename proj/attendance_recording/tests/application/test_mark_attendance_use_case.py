from datetime import datetime, timedelta

from attendance_recording.application.use_cases.mark_attendance import MarkAttendanceUseCase
from attendance_recording.domain.entities.attendance import Attendance
from attendance_recording.domain.exceptions import DuplicateAttendanceError


class FakeTokenValidator:
	def validate_and_decode(self, token: str):
		return {"student_profile_id": 45, "session_id": 67}


class FakeAttendanceService:
	def mark_attendance(
		self,
		token: str,
		qr_code: str,
		latitude: float,
		longitude: float,
		session_id: int,
		session_latitude: float,
		session_longitude: float,
		session_start_time,
		session_end_time,
		session_program_id: str,
		student_program_id: str,
		student_stream=None,
		session_stream=None,
		student_is_active: bool = True,
		expected_student_id: str | None = None,
	):
		# Minimal: return an Attendance entity; repository will assign ID
		return Attendance.create(
			student_id=45,
			session_id=session_id,
			time_recorded=datetime(2025, 10, 25, 8, 5, 23),
			latitude=latitude,
			longitude=longitude,
			status="present",
			is_within_radius=True,
		)


class FakeRepo:
	def __init__(self, exists=False):
		self._exists = exists
		self.created = []

	def exists_for_student_and_session(self, student_profile_id: int, session_id: int) -> bool:
		return self._exists

	def create(self, attendance: Attendance) -> Attendance:
		# Assign a fake ID and return
		obj = Attendance(
			attendance_id=123,
			student_id=attendance.student_id,
			session_id=attendance.session_id,
			time_recorded=attendance.time_recorded,
			latitude=attendance.latitude,
			longitude=attendance.longitude,
			status=attendance.status,
			is_within_radius=attendance.is_within_radius,
		)
		self.created.append(obj)
		return obj


def fake_session_provider(session_id: int):
	return {
		"latitude": -1.28334,
		"longitude": 36.81667,
		"start_time": datetime.now() - timedelta(minutes=30),
		"end_time": datetime.now() + timedelta(minutes=30),
		"program_id": "BCS",
		"stream_id": "A",
	}


def fake_student_provider(student_profile_id: int):
	return {
		"student_profile_id": 45,
		"program_id": "BCS",
		"stream_id": "A",
		"is_active": True,
		"student_id": "BCS/123456",
	}


def test_use_case_success_returns_dto():
	uc = MarkAttendanceUseCase(
		attendance_service=FakeAttendanceService(),
		token_validator=FakeTokenValidator(),
		attendance_repository=FakeRepo(exists=False),
		session_provider=fake_session_provider,
		student_provider=fake_student_provider,
	)

	dto = uc.execute(
		token="abc.def.ghi",
		qr_code="BCS/123456",
		latitude=-1.28334,
		longitude=36.81667,
	)

	assert dto.attendance_id == 123
	assert dto.student_profile_id == 45
	assert dto.session_id == 67
	assert dto.status == "present"
	assert dto.is_within_radius is True


def test_use_case_duplicate_raises():
	uc = MarkAttendanceUseCase(
		attendance_service=FakeAttendanceService(),
		token_validator=FakeTokenValidator(),
		attendance_repository=FakeRepo(exists=True),
		session_provider=fake_session_provider,
		student_provider=fake_student_provider,
	)

	try:
		uc.execute(
			token="abc.def.ghi",
			qr_code="BCS/123456",
			latitude=-1.28334,
			longitude=36.81667,
		)
		assert False, "Expected DuplicateAttendanceError"
	except DuplicateAttendanceError:
		pass
