"""Session provider adapter returning data for application use case."""
from __future__ import annotations

from typing import Dict, Any

from session_management.models import Session


def get_session_info(session_id: int) -> Dict[str, Any]:
	"""Retrieve session details mapped to use-case expected keys.

	Returns a dict with latitude, longitude, start/end times, program_id, stream_id.
	"""
	try:
		session = Session.objects.select_related("program", "stream").get(session_id=session_id)
	except Session.DoesNotExist:
		return {}

	return {
		"latitude": float(session.latitude),
		"longitude": float(session.longitude),
		"start_time": session.time_created,
		"end_time": session.time_ended,
		"program_id": getattr(session, "program_id", None),
		"stream_id": getattr(session, "stream_id", None),
	}
