"""Student provider adapter returning data for application use case."""
from __future__ import annotations

from typing import Dict, Any

from user_management.models import StudentProfile


def get_student_info(student_profile_id: int) -> Dict[str, Any]:
	"""Retrieve student profile details mapped to use-case keys.

	Includes program/stream, active flag, and student_id code.
	"""
	try:
		sp = (
			StudentProfile.objects.select_related("user", "program", "stream")
			.get(student_profile_id=student_profile_id)
		)
	except StudentProfile.DoesNotExist:
		return {}

	return {
		"student_profile_id": sp.student_profile_id,
		"program_id": getattr(sp, "program_id", None),
		"stream_id": getattr(sp, "stream_id", None),
		"is_active": bool(getattr(sp.user, "is_active", True)),
		"student_id": sp.student_id,
	}
