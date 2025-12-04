"""Custom permissions for Session Management API."""

from rest_framework import permissions


class IsLecturer(permissions.BasePermission):
    """Permission check: user must be a lecturer."""
    
    message = "Only lecturers can access this resource."
    
    def has_permission(self, request, view):
        """Check if user is authenticated and has lecturer role."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has lecturer role
        return hasattr(request.user, 'role') and request.user.role == 'Lecturer'


class IsSessionOwner(permissions.BasePermission):
    """Permission check: user must be the session owner (lecturer who created it)."""
    
    message = "You do not have permission to access this session."
    
    def has_object_permission(self, request, view, obj):
        """Check if user is the session owner."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # obj is the session DTO dict, check lecturer_id
        if isinstance(obj, dict):
            lecturer_id = obj.get('lecturer_id')
        else:
            lecturer_id = getattr(obj, 'lecturer_id', None)
        
        # Get lecturer profile ID from user
        if hasattr(request.user, 'lecturer_profile'):
            return request.user.lecturer_profile.lecturer_id == lecturer_id
        
        return False
