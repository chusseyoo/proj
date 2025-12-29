"""AttendanceRepository implementation using Django ORM.

Provides CRUD, duplicate checks, session/student queries, and statistics
aligned with repositories_guide.md spec.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from django.db import IntegrityError
from django.db.models import Count, QuerySet

from attendance_recording.domain.entities.attendance import Attendance as DomainAttendance
from attendance_recording.domain.exceptions import DuplicateAttendanceError
from attendance_recording.infrastructure.orm.django_models import Attendance as ORMAttendance


class AttendanceRepositoryImpl:
	"""Concrete repository bridging domain `Attendance` to Django ORM.
	
	Implements all methods from repositories_guide.md:
	- CRUD (create, get_by_id, delete)
	- Duplicate detection (exists_for_student_and_session)
	- Session queries (get_by_session, count_by_session, etc.)
	- Student queries (get_by_student, count_by_student)
	- Reporting queries
	"""

	# ==================== CRUD Operations ====================

	def create(self, attendance: DomainAttendance) -> DomainAttendance:
		"""Persist a domain attendance entity and return with assigned ID.

		Maps the domain entity to ORM fields and catches duplicates.
		Per docs: takes domain entity (adapted from dict signature in docs).
		"""
		try:
			obj = ORMAttendance.objects.create(
				student_profile_id=attendance.student_id,
				session_id=attendance.session_id,
				latitude=attendance.latitude,
				longitude=attendance.longitude,
				status=attendance.status,
				is_within_radius=attendance.is_within_radius,
			)
		except IntegrityError:
			# Unique constraint violation -> duplicate attendance
			raise DuplicateAttendanceError(attendance.student_id, attendance.session_id)

		# Return updated domain entity with assigned PK and ORM timestamp
		return DomainAttendance(
			attendance_id=obj.attendance_id,
			student_id=attendance.student_id,
			session_id=attendance.session_id,
			time_recorded=obj.time_recorded,  # Use ORM auto-generated timestamp
			latitude=attendance.latitude,
			longitude=attendance.longitude,
			status=attendance.status,
			is_within_radius=attendance.is_within_radius,
		)

	def get_by_id(self, attendance_id: int) -> ORMAttendance:
		"""Retrieve attendance record by primary key.
		
		Raises: ORMAttendance.DoesNotExist if not found
		Optimization: Uses select_related for related data
		"""
		return ORMAttendance.objects.select_related(
			"student_profile__user", "session"
		).get(attendance_id=attendance_id)

	def delete(self, attendance_id: int) -> None:
		"""Hard delete attendance record.
		
		Use case: Lecturer removes mistaken attendance (rare).
		Note: Should verify lecturer owns the session before calling.
		"""
		ORMAttendance.objects.filter(attendance_id=attendance_id).delete()

	# ==================== Duplicate Detection ====================

	def exists_for_student_and_session(self, student_profile_id: int, session_id: int) -> bool:
		"""Check if attendance already exists (fast duplicate check)."""
		return ORMAttendance.objects.filter(
			student_profile_id=student_profile_id,
			session_id=session_id,
		).exists()

	def get_by_student_and_session(
		self, student_profile_id: int, session_id: int
	) -> Optional[ORMAttendance]:
		"""Retrieve existing attendance if any."""
		return (
			ORMAttendance.objects.filter(
				student_profile_id=student_profile_id,
				session_id=session_id,
			)
			.select_related("student_profile__user", "session")
			.first()
		)

	# ==================== Session-Based Queries ====================

	def get_by_session(self, session_id: int) -> QuerySet[ORMAttendance]:
		"""Get all attendance records for a session, ordered by time."""
		return (
			ORMAttendance.objects.filter(session_id=session_id)
			.select_related("student_profile__user")
			.order_by("time_recorded")
		)

	def get_by_session_with_status(self, session_id: int, status: str) -> QuerySet[ORMAttendance]:
		"""Filter session attendance by status (present/late)."""
		return (
			ORMAttendance.objects.filter(session_id=session_id, status=status)
			.select_related("student_profile__user")
			.order_by("time_recorded")
		)

	def count_by_session(self, session_id: int) -> dict:
		"""Get attendance statistics for session.
		
		Returns dict with total, present, late counts.
		Note: absent count requires cross-context query (eligible students).
		"""
		counts = (
			ORMAttendance.objects.filter(session_id=session_id)
			.values("status")
			.annotate(count=Count("status"))
		)
		
		result = {"total": 0, "present": 0, "late": 0}
		for item in counts:
			status = item["status"]
			count = item["count"]
			result["total"] += count
			if status == "present":
				result["present"] = count
			elif status == "late":
				result["late"] = count
		
		return result

	def get_students_outside_radius(self, session_id: int) -> QuerySet[ORMAttendance]:
		"""Find students who marked attendance outside 30m radius (fraud detection)."""
		return (
			ORMAttendance.objects.filter(session_id=session_id, is_within_radius=False)
			.select_related("student_profile__user")
			.order_by("time_recorded")
		)

	# ==================== Student-Based Queries ====================

	def get_by_student(
		self, student_profile_id: int, limit: Optional[int] = None
	) -> QuerySet[ORMAttendance]:
		"""Get student's attendance history, most recent first."""
		qs = (
			ORMAttendance.objects.filter(student_profile_id=student_profile_id)
			.select_related("session__course")
			.order_by("-time_recorded")
		)
		if limit:
			qs = qs[:limit]
		return qs

	def count_by_student(self, student_profile_id: int) -> dict:
		"""Get student's attendance statistics.
		
		Returns dict with total_attended, present, late counts.
		Note: attendance_rate requires total eligible sessions (cross-context).
		"""
		counts = (
			ORMAttendance.objects.filter(student_profile_id=student_profile_id)
			.values("status")
			.annotate(count=Count("status"))
		)
		
		result = {"total_attended": 0, "present": 0, "late": 0}
		for item in counts:
			status = item["status"]
			count = item["count"]
			result["total_attended"] += count
			if status == "present":
				result["present"] = count
			elif status == "late":
				result["late"] = count
		
		return result

	def get_by_student_and_course(
		self, student_profile_id: int, course_id: int
	) -> QuerySet[ORMAttendance]:
		"""Get student's attendance for a specific course."""
		return (
			ORMAttendance.objects.filter(
				student_profile_id=student_profile_id, session__course_id=course_id
			)
			.select_related("session")
			.order_by("-time_recorded")
		)

	# ==================== Time-Based Queries ====================

	def get_by_date_range(self, start_date: date, end_date: date) -> QuerySet[ORMAttendance]:
		"""Get all attendance within date range."""
		return (
			ORMAttendance.objects.filter(
				time_recorded__date__gte=start_date, time_recorded__date__lte=end_date
			)
			.select_related("student_profile__user", "session")
			.order_by("-time_recorded")
		)

	def get_recent_attendance(self, hours: int = 24) -> QuerySet[ORMAttendance]:
		"""Get recently recorded attendance (default: last 24 hours)."""
		from django.utils import timezone
		from datetime import timedelta

		cutoff = timezone.now() - timedelta(hours=hours)
		return (
			ORMAttendance.objects.filter(time_recorded__gte=cutoff)
			.select_related("student_profile__user", "session")
			.order_by("-time_recorded")
		)

