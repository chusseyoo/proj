"""API views for Email Notifications.

Endpoints per docs:
- POST /internal/sessions/{session_id}/notifications
- POST /admin/notifications/retry
- GET /sessions/{session_id}/notifications
- GET /admin/notifications/statistics
"""

from typing import Any, Dict, List

from django.conf import settings
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from email_notifications.application.use_cases.generate_notifications import (
    GenerateNotificationsForSession,
)
from email_notifications.application.use_cases.retry_failed_notifications import (
    RetryFailedNotifications,
)
from email_notifications.application.use_cases.list_notifications import (
    ListNotificationsForSession,
)
from email_notifications.application.use_cases.get_notification_statistics import (
    GetNotificationStatistics,
)
from email_notifications.domain.services.jwt_service import JWTTokenService
from email_notifications.domain.services.notification_generation_service import (
    NotificationGenerationService,
)
from email_notifications.interfaces.api.permissions import (
    IsInternalService,
    IsSessionOwnerOrAdmin,
)
from user_management.interfaces.api.permissions import IsAdmin
from user_management.interfaces.api.authentication import JWTAuthentication
from email_notifications.interfaces.api.serializers import (
    GenerateNotificationsResponseSerializer,
    RetryRequestSerializer,
    RetryResponseSerializer,
    ListQuerySerializer,
    PaginatedListResponseSerializer,
    StatisticsQuerySerializer,
    StatisticsResponseSerializer,
)


# Providers for use cases
def _session_provider(session_id: int) -> Dict[str, Any]:
    from session_management.infrastructure.orm.django_models import Session

    try:
        s = (
            Session.objects.select_related("program", "stream", "lecturer__user")
            .get(session_id=session_id)
        )
    except Session.DoesNotExist:
        return {}

    return {
        "session_id": s.session_id,
        # Treat time_created as session start (per model)
        "start_time": s.time_created,
        "program_id": s.program_id,
        "stream_id": s.stream_id,
    }


def _eligible_students_provider(session_dict: Dict[str, Any]) -> List[Dict[str, int]]:
    from user_management.infrastructure.orm.django_models import StudentProfile

    program_id = session_dict.get("program_id")
    stream_id = session_dict.get("stream_id")

    qs = StudentProfile.objects.select_related("user").filter(
        program_id=program_id,
        user__is_active=True,
    )
    if stream_id is not None:
        qs = qs.filter(stream_id=stream_id)

    return [{"student_profile_id": sp.student_profile_id} for sp in qs]


def _student_enricher(student_profile_id: int) -> Dict[str, Any]:
    from user_management.infrastructure.orm.django_models import StudentProfile

    try:
        sp = StudentProfile.objects.select_related("user").get(
            student_profile_id=student_profile_id
        )
    except StudentProfile.DoesNotExist:
        return {}

    return {
        "name": sp.user.get_full_name(),
        "email": sp.user.email,
    }


class InternalGenerateNotificationsView(APIView):
    permission_classes = [IsInternalService]

    def post(self, request, session_id: int) -> Response:
        jwt_secret = getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY)
        jwt_service = JWTTokenService(secret_key=jwt_secret)
        notif_service = NotificationGenerationService(jwt_service=jwt_service)

        use_case = GenerateNotificationsForSession(
            session_provider=_session_provider,
            students_provider=_eligible_students_provider,
            notification_service=notif_service,
        )

        result = use_case.execute(session_id=session_id)
        serializer = GenerateNotificationsResponseSerializer(data=result)
        serializer.is_valid(raise_exception=True)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_201_CREATED)


class AdminRetryFailedView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]

    def post(self, request) -> Response:
        serializer = RetryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = RetryFailedNotifications()
        result = use_case.execute(email_ids=serializer.validated_data["email_ids"])

        resp = RetryResponseSerializer(data=result)
        resp.is_valid(raise_exception=True)
        return Response({"status": "success", "data": resp.data}, status=status.HTTP_200_OK)


class SessionNotificationsListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSessionOwnerOrAdmin]

    def get(self, request, session_id: int) -> Response:
        query = ListQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)

        use_case = ListNotificationsForSession(student_enricher=_student_enricher)
        result = use_case.execute(
            session_id=session_id,
            status=query.validated_data.get("status"),
            page=query.validated_data.get("page", 1),
            page_size=query.validated_data.get("page_size", 20),
        )

        resp = PaginatedListResponseSerializer(data=result)
        resp.is_valid(raise_exception=True)
        return Response(resp.data, status=status.HTTP_200_OK)


class AdminStatisticsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]

    def get(self, request) -> Response:
        query = StatisticsQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)

        use_case = GetNotificationStatistics()
        result = use_case.execute(session_id=query.validated_data.get("session_id"))

        resp = StatisticsResponseSerializer(data=result)
        resp.is_valid(raise_exception=True)
        return Response(resp.data, status=status.HTTP_200_OK)
