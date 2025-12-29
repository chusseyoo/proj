"""URL routing for attendance recording API endpoints."""
from django.urls import path
from attendance_recording.interfaces.api.views import MarkAttendanceView

app_name = 'attendance_recording'

urlpatterns = [
    path('api/v1/attendance/mark', MarkAttendanceView.as_view(), name='mark_attendance'),
]
