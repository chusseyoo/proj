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
from typing import List, Any, Iterable, Dict, Optional
from datetime import datetime

from reporting.application.dto.report_dto import StudentRowDTO


class AttendanceAggregator:
    """Construct student rows and classify presence according to the
    canonical rule.

    Implementation notes:
    - `session` must expose `start_time` and `end_time` as datetime objects.
    - `eligible_students` is an iterable of objects/dicts with at least
      `student_id`, `student_name`, `email`, `program`, `stream`.
    - `attendance_records` is an iterable of dict-like objects with keys:
      `student_id`, `time_recorded` (datetime or ISO string), `within_radius` (bool),
      `latitude`, `longitude`, `status`.

    The aggregator classifies a student as "Present" if any attendance
    record for that student meets BOTH: time_recorded in [start_time, end_time]
    (inclusive) AND within_radius is True. Otherwise the student is
    "Absent". Diagnostic fields are populated from the best-available
    attendance record (preference: qualifying record; else latest record).
    """

    def classify(self, session: Any, eligible_students: Iterable[Any], attendance_records: Iterable[Any]) -> List[StudentRowDTO]:
        start_time: datetime = session.start_time
        end_time: datetime = session.end_time

        # Group attendance records by student_id
        records_by_student: Dict[str, List[Dict]] = {}
        for r in attendance_records:
            sid = r.get("student_id")
            if sid is None:
                continue
            records_by_student.setdefault(sid, []).append(r)

        rows: List[StudentRowDTO] = []

        for s in eligible_students:
            # support dict-like or object
            sid = s.get("student_id") if isinstance(s, dict) else getattr(s, "student_id")
            name = s.get("student_name") if isinstance(s, dict) else getattr(s, "student_name", None)
            email = s.get("email") if isinstance(s, dict) else getattr(s, "email", None)
            program = s.get("program") if isinstance(s, dict) else getattr(s, "program", None)
            stream = s.get("stream") if isinstance(s, dict) else getattr(s, "stream", None)

            student_records = records_by_student.get(sid, [])

            # Find qualifying records (in-window AND within_radius True)
            qualifying: List[Dict] = []
            for rec in student_records:
                tr = rec.get("time_recorded")
                # accept both str and datetime; prefer datetime for comparison
                if isinstance(tr, str):
                    try:
                        tr = datetime.fromisoformat(tr)
                    except Exception:
                        # unparseable times are ignored
                        continue
                if not isinstance(tr, datetime):
                    continue
                within = rec.get("within_radius") is True
                if tr >= start_time and tr <= end_time and within:
                    qualifying.append({**rec, "time_recorded": tr})

            status = "Absent"
            chosen_rec: Optional[Dict] = None

            if qualifying:
                # pick the earliest qualifying record for diagnostics
                chosen_rec = sorted(qualifying, key=lambda x: x["time_recorded"])[0]
                status = "Present"
            elif student_records:
                # no qualifying record; choose the latest record for diagnostics
                # normalize time_recorded to datetime where possible
                normalized = []
                for rec in student_records:
                    tr = rec.get("time_recorded")
                    if isinstance(tr, str):
                        try:
                            tr = datetime.fromisoformat(tr)
                        except Exception:
                            tr = None
                    normalized.append({**rec, "time_recorded": tr})
                # prefer latest by time_recorded, put None times last
                normalized_sorted = sorted(normalized, key=lambda x: (x["time_recorded"] is None, x["time_recorded"]))
                chosen_rec = normalized_sorted[-1]
                status = "Absent"

            # prepare diagnostics
            if chosen_rec:
                tr = chosen_rec.get("time_recorded")
                time_iso = tr.isoformat() if isinstance(tr, datetime) else None
                within_radius = chosen_rec.get("within_radius")
                lat = chosen_rec.get("latitude")
                lon = chosen_rec.get("longitude")
            else:
                time_iso = None
                within_radius = None
                lat = None
                lon = None

            row = StudentRowDTO(
                student_id=str(sid),
                student_name=name,
                email=email,
                program=program,
                stream=stream,
                status=status,
                time_recorded=time_iso,
                within_radius=within_radius,
                latitude=str(lat) if lat is not None else None,
                longitude=str(lon) if lon is not None else None,
            )

            rows.append(row)

        return rows
