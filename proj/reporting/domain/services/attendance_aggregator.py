"""Attendance aggregation and classification logic.

Canonical rule (enforced by this service): A student is classified as
"Present" iff ALL of:
  - there is at least one attendance record for the student for the session,
  - the attendance.time_recorded is within the session window
    (>= session.start_time and <= session.end_time), and
  - attendance.within_radius is True.

All other attendance records are retained for diagnostics but do not
count toward the official `present_count`.
"""
from typing import List, Any

from reporting.application.dto.report_dto import StudentRowDTO


class AttendanceAggregator:
    """Construct student rows and classify presence according to the
    canonical rule.

    This scaffold exposes the public API; implementation should iterate
    eligible students and attendance records, applying the three checks
    above.
    """

    def classify(self, session: Any, eligible_students: List[Any], attendance_records: List[Any]) -> List[StudentRowDTO]:
        """Return a list of StudentRowDTO for the report.

        Parameters
        - session: session object (must expose start_time and end_time)
        - eligible_students: iterable of student profile objects
        - attendance_records: iterable of attendance objects (with student id,
          time_recorded, within_radius, latitude, longitude, status)

        Behaviour: For each eligible student, produce a StudentRowDTO with
        `status` set to "Present" only when a qualifying attendance record
        exists (time window AND within_radius). Otherwise "Absent".
        """
        # TODO: implement classification algorithm (time window + radius)
        raise NotImplementedError("AttendanceAggregator.classify not implemented")
