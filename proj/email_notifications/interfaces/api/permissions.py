"""Permissions for Email Notifications API.

Implements:
- IsInternalService: checks for internal service token in header
- IsSessionOwnerOrAdmin: lecturer who owns the session or admin
"""

import os
from typing import Optional

from django.conf import settings
from rest_framework import permissions


class IsInternalService(permissions.BasePermission):
    """Allow only internal services authenticated via shared token header.

    Expects header: X-Internal-Token: <shared_secret>
    Compares against settings.EMAIL_NOTIFICATIONS_INTERNAL_TOKEN or env INTERNAL_SERVICE_TOKEN.
    """

    HEADER_NAME = "HTTP_X_INTERNAL_TOKEN"  # Django WSGI format for X-Internal-Token

    def _get_expected_token(self) -> Optional[str]:
        # Prefer explicit setting, fallback to environment
        token = getattr(settings, "EMAIL_NOTIFICATIONS_INTERNAL_TOKEN", None)
        if token:
            return token
        return os.environ.get("INTERNAL_SERVICE_TOKEN")

    def has_permission(self, request, view) -> bool:
        expected = self._get_expected_token()
        provided = request.META.get(self.HEADER_NAME)

        if not expected or not provided:
            return False

        # Constant-time compare is overkill here but fine for symmetry
        try:
            from hmac import compare_digest
            return compare_digest(str(provided), str(expected))
        except Exception:
            return str(provided) == str(expected)


class IsSessionOwnerOrAdmin(permissions.BasePermission):
    """Allow if user is Admin or Lecturer who owns the session.

    Requires `session_id` in URL kwargs.
    """

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        # Accept domain user entities (no is_authenticated attr) as authenticated
        if not user or not hasattr(user, "user_id"):
            return False

        # Admins allowed
        if hasattr(user, "is_admin") and user.is_admin():
            return True

        # If no session_id available yet, defer to object permission (deny by default)
        session_id = view.kwargs.get("session_id") if hasattr(view, "kwargs") else None
        if not session_id:
            return False

        # Lecturer must own the session
        try:
            from session_management.infrastructure.orm.django_models import Session
        except Exception:
            return False

        try:
            session = Session.objects.select_related("lecturer__user").get(session_id=session_id)
        except Session.DoesNotExist:
            return False

        lecturer_user_id = getattr(getattr(session, "lecturer", None), "user_id", None)
        return lecturer_user_id is not None and lecturer_user_id == getattr(user, "user_id", None)
