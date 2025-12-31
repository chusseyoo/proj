"""DRF permissions for reporting API endpoints."""
from rest_framework import permissions


class IsLecturerOrAdmin(permissions.BasePermission):
    """Permission: user must be a lecturer or admin (not student)."""

    def has_permission(self, request, view):
        if not request.user:
            return False

        role = getattr(request.user, 'role', None)
        return role in ['lecturer', 'admin']


class IsSessionOwnerOrAdmin(permissions.BasePermission):
    """Permission: user must own the session or be admin."""

    def has_permission(self, request, view):
        if not request.user:
            return False
        
        role = getattr(request.user, 'role', None)
        if role == 'admin':
            return True
        
        if role != 'lecturer':
            return False
        
        # Check session ownership
        session_id = view.kwargs.get('session_id')
        if not session_id:
            return False
        
        try:
            from session_management.infrastructure.orm.django_models import Session
            session = Session.objects.get(pk=session_id)
            return session.lecturer_id == getattr(request.user, 'id', None)
        except Exception:
            return False


class IsReportOwnerOrAdmin(permissions.BasePermission):
    """Permission: user owns the report's session or is admin."""

    def has_permission(self, request, view):
        if not request.user:
            return False
        
        role = getattr(request.user, 'role', None)
        if role == 'admin':
            return True
        
        if role != 'lecturer':
            return False
        
        # Check report ownership
        report_id = view.kwargs.get('report_id')
        if not report_id:
            return False
        
        try:
            from reporting.models import Report
            from session_management.infrastructure.orm.django_models import Session
            
            report = Report.objects.select_related().get(pk=report_id)
            session = Session.objects.get(pk=report.session_id)
            return session.lecturer_id == getattr(request.user, 'id', None)
        except Exception:
            return False


class IsAdminUser(permissions.BasePermission):
    """Permission: user must be admin."""

    def has_permission(self, request, view):
        if not request.user:
            return False
        
        role = getattr(request.user, 'role', None)
        return role == 'admin'
