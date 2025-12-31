"""Domain service that generates report data from session, students, and attendance records."""
from typing import Any, Iterable

from reporting.domain.services.attendance_aggregator import AttendanceAggregator
from reporting.domain.value_objects.report_generation_result import ReportGenerationResult
from reporting.domain.value_objects.report_statistics import ReportStatistics


class ReportGenerator:
    def __init__(self, attendance_aggregator: AttendanceAggregator | None = None):
        self.aggregator = attendance_aggregator or AttendanceAggregator()

    def generate(self, session: Any, eligible_students: Iterable[Any], attendance_records: Iterable[Any]) -> ReportGenerationResult:
        students = self.aggregator.classify(session, eligible_students, attendance_records)
        stats = ReportStatistics.from_rows([s.to_dict() for s in students])
        return ReportGenerationResult(session=session, students=students, statistics=stats)
