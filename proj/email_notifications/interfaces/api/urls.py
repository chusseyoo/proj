from django.urls import path

from email_notifications.interfaces.api.views import (
    InternalGenerateNotificationsView,
    AdminRetryFailedView,
    SessionNotificationsListView,
    AdminStatisticsView,
)


app_name = "email_notifications_api"


urlpatterns = [
    # Internal
    path(
        "internal/sessions/<int:session_id>/notifications",
        InternalGenerateNotificationsView.as_view(),
        name="internal-generate-notifications",
    ),
    # Admin
    path(
        "admin/notifications/retry",
        AdminRetryFailedView.as_view(),
        name="admin-retry-failed",
    ),
    path(
        "admin/notifications/statistics",
        AdminStatisticsView.as_view(),
        name="admin-statistics",
    ),
    # Monitoring
    path(
        "sessions/<int:session_id>/notifications",
        SessionNotificationsListView.as_view(),
        name="session-notifications-list",
    ),
]
