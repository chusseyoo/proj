"""URL configuration for Session Management API."""

from django.urls import path
from .views import (
    SessionListCreateView,
    SessionDetailView,
    SessionEndNowView,
)

app_name = 'session_management_api'

urlpatterns = [
    # Session CRUD endpoints
    path('sessions/', SessionListCreateView.as_view(), name='session-list-create'),
    path('sessions/<int:session_id>/', SessionDetailView.as_view(), name='session-detail'),
    path('sessions/<int:session_id>/end-now/', SessionEndNowView.as_view(), name='session-end-now'),
]
