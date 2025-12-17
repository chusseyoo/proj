from django.contrib import admin, messages

from email_notifications.models import EmailNotification
from email_notifications.application.use_cases.retry_failed_notifications import (
    RetryFailedNotifications,
)


@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = ("email_id", "session", "student_profile", "status", "created_at", "sent_at")
    list_filter = ("status", "created_at", "session")
    search_fields = ("email_id", "session__session_id", "student_profile__student_id")
    actions = ["retry_failed_notifications_action"]

    @admin.action(description="Retry selected failed notifications")
    def retry_failed_notifications_action(self, request, queryset):
        failed_ids = list(
            queryset.filter(status=EmailNotification.Status.FAILED).values_list("email_id", flat=True)
        )

        if not failed_ids:
            self.message_user(
                request,
                "No failed notifications selected. Only failed notifications can be retried.",
                level=messages.WARNING,
            )
            return

        use_case = RetryFailedNotifications()
        result = use_case.execute(email_ids=failed_ids)

        msg = f"Retried: {result['retried']} | Skipped: {result['skipped']}"
        if result.get("errors"):
            msg += f" | Errors: {len(result['errors'])}"
            level = messages.WARNING
        else:
            level = messages.SUCCESS
        self.message_user(request, msg, level=level)

    def changelist_view(self, request, extra_context=None):
        """Show system-wide stats as an info banner (no custom template)."""
        from email_notifications.application.use_cases.get_notification_statistics import (
            GetNotificationStatistics,
        )

        extra_context = extra_context or {}
        stats = GetNotificationStatistics().execute()
        stats_msg = (
            f"System Stats — Total: {stats['total']} | "
            f"Sent: {stats['sent']} | Failed: {stats['failed']} | "
            f"Pending: {stats['pending']} | Success Rate: {stats['success_rate']}%"
        )
        # Show on each visit to keep it fresh
        self.message_user(request, stats_msg, level=messages.INFO)
        return super().changelist_view(request, extra_context)
