"""DRF serializers for reporting API endpoints."""
try:
    from rest_framework import serializers
except Exception:  # pragma: no cover
    class serializers:  # type: ignore
        class Serializer:  # type: ignore
            pass


class ExportReportRequestSerializer(serializers.Serializer):
    """Request validation for export endpoint."""
    file_type = serializers.ChoiceField(choices=["csv", "excel"], required=True)


class StatisticsDTOSerializer(serializers.Serializer):
    """Statistics nested object in report response."""
    total_students = serializers.IntegerField()
    present_count = serializers.IntegerField()
    present_percentage = serializers.FloatField()
    absent_count = serializers.IntegerField()
    absent_percentage = serializers.FloatField()
    within_radius_count = serializers.IntegerField(required=False)
    outside_radius_count = serializers.IntegerField(required=False)


class StudentRowDTOSerializer(serializers.Serializer):
    """Individual student row in report."""
    student_id = serializers.CharField()
    student_name = serializers.CharField()
    email = serializers.CharField()
    program = serializers.CharField()
    stream = serializers.CharField(allow_blank=True, required=False)
    status = serializers.ChoiceField(choices=["Present", "Absent"])
    time_recorded = serializers.DateTimeField(allow_null=True, required=False)
    within_radius = serializers.BooleanField(allow_null=True, required=False)
    latitude = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    longitude = serializers.CharField(allow_blank=True, allow_null=True, required=False)


class SessionInfoSerializer(serializers.Serializer):
    """Session information nested in report response."""
    session_id = serializers.IntegerField()
    course_name = serializers.CharField()
    course_code = serializers.CharField()
    program_name = serializers.CharField()
    program_code = serializers.CharField(allow_blank=True)
    stream_name = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    time_created = serializers.DateTimeField()
    time_ended = serializers.DateTimeField()
    lecturer_name = serializers.CharField()


class ReportResponseSerializer(serializers.Serializer):
    """Full report response with session, statistics, students."""
    report_id = serializers.IntegerField()
    session = SessionInfoSerializer()
    statistics = StatisticsDTOSerializer()
    students = StudentRowDTOSerializer(many=True)
    generated_date = serializers.DateTimeField()
    generated_by = serializers.CharField()
    export_status = serializers.ChoiceField(choices=["exported", "not_exported"])


class ExportResultSerializer(serializers.Serializer):
    """Export result response."""
    report_id = serializers.IntegerField()
    file_type = serializers.CharField()
    download_url = serializers.CharField()
    generated_date = serializers.DateTimeField()


class ReportListItemSerializer(serializers.Serializer):
    """Single report item in list response."""
    report_id = serializers.IntegerField()
    session_id = serializers.IntegerField()
    session_name = serializers.CharField()
    generated_by = serializers.CharField()
    generated_date = serializers.DateTimeField()
    export_status = serializers.ChoiceField(choices=["exported", "not_exported"])
    file_type = serializers.CharField(allow_blank=True, allow_null=True, required=False)


class PaginationSerializer(serializers.Serializer):
    """Pagination info."""
    current_page = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    total_reports = serializers.IntegerField()
    page_size = serializers.IntegerField()


class ReportListResponseSerializer(serializers.Serializer):
    """List reports response."""
    reports = ReportListItemSerializer(many=True)
    pagination = PaginationSerializer()
