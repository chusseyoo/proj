"""Container for generated report data at the domain layer."""
from dataclasses import dataclass
from typing import Any, List

from reporting.domain.value_objects.report_statistics import ReportStatistics
from reporting.domain.value_objects.student_attendance_row import StudentAttendanceRow


@dataclass
class ReportGenerationResult:
    session: Any
    students: List[StudentAttendanceRow]
    statistics: ReportStatistics

    def to_metadata(self) -> dict:
        """Return a serializable dict suitable for persistence/export."""
        return {
            "session": self.session,
            "students": [s.to_dict() for s in self.students],
            "statistics": self.statistics.to_dict(),
        }
