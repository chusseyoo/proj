"""DRF serializers for email notifications API."""
from rest_framework import serializers

from email_notifications.application.dto import EmailNotificationDTO


class EmailNotificationSerializer(serializers.Serializer):
    """Response serializer for EmailNotification DTO."""

    email_id = serializers.IntegerField()
    session_id = serializers.IntegerField()
    student_profile_id = serializers.IntegerField()
    student_name = serializers.CharField(allow_null=True, required=False)
    student_email = serializers.EmailField(allow_null=True, required=False)
    token_expires_at = serializers.DateTimeField()
    status = serializers.ChoiceField(choices=["pending", "sent", "failed"])
    created_at = serializers.DateTimeField()
    sent_at = serializers.DateTimeField(allow_null=True)


class RetryRequestSerializer(serializers.Serializer):
    """Request serializer for admin retry endpoint."""

    email_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        min_length=1,
        help_text="List of email notification IDs to retry",
    )


class ListQuerySerializer(serializers.Serializer):
    """Query params serializer for list notifications endpoint."""

    status = serializers.ChoiceField(
        choices=["pending", "sent", "failed"],
        required=False,
        allow_null=True,
        help_text="Filter by status",
    )
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20)


class StatisticsQuerySerializer(serializers.Serializer):
    """Query params for statistics endpoint."""

    session_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)


class GenerateNotificationsResponseSerializer(serializers.Serializer):
    """Response for internal generate notifications endpoint."""

    session_id = serializers.IntegerField()
    notifications_created = serializers.IntegerField()
    eligible_students = serializers.IntegerField()


class RetryResponseSerializer(serializers.Serializer):
    """Response for admin retry endpoint."""

    retried = serializers.IntegerField()
    skipped = serializers.IntegerField()
    errors = serializers.ListField(child=serializers.CharField())


class PaginatedListResponseSerializer(serializers.Serializer):
    """Paginated response for list notifications."""

    results = EmailNotificationSerializer(many=True)
    total_count = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    has_next = serializers.BooleanField()
    has_previous = serializers.BooleanField()


class StatisticsResponseSerializer(serializers.Serializer):
    """Response for statistics endpoint."""

    total = serializers.IntegerField()
    pending = serializers.IntegerField()
    sent = serializers.IntegerField()
    failed = serializers.IntegerField()
    success_rate = serializers.FloatField()
