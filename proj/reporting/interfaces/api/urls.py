"""URL routing for reporting context (scaffold)."""
from django.urls import path
from .views import GenerateReportView

urlpatterns = [
    path('sessions/<int:session_id>/report/', GenerateReportView.as_view(), name='generate_report'),
]
