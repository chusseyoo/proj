"""URL routing for reporting context."""
from django.urls import path

from .views import (
    GenerateReportView,
    ViewReportView,
    ExportReportView,
    DownloadReportView,
    ListReportsView,
)

urlpatterns = [
    # Generate new report for a session
    path(
        "api/v1/sessions/<int:session_id>/report/",
        GenerateReportView.as_view(),
        name="generate_report",
    ),
    # View specific report
    path(
        "api/v1/reports/<int:report_id>/",
        ViewReportView.as_view(),
        name="view_report",
    ),
    # Export report to CSV or Excel
    path(
        "api/v1/reports/<int:report_id>/export/",
        ExportReportView.as_view(),
        name="export_report",
    ),
    # Download exported report file
    path(
        "api/v1/reports/<int:report_id>/download/",
        DownloadReportView.as_view(),
        name="download_report",
    ),
    # List all reports (admin only)
    path(
        "api/v1/reports/",
        ListReportsView.as_view(),
        name="list_reports",
    ),
]

