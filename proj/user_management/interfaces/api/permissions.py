"""
DRF Permission Classes for Role-Based Access Control.

Implements role checks for Admin, Lecturer, Student,
and owner-or-admin policies.
"""
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission: Only Admin role can access.
    """
    
    def has_permission(self, request, view):
        return bool(
            request.user
            and hasattr(request.user, 'is_admin')
            and request.user.is_admin()
        )


class IsLecturer(permissions.BasePermission):
    """
    Permission: Only Lecturer role can access.
    """
    
    def has_permission(self, request, view):
        return bool(
            request.user
            and hasattr(request.user, 'is_lecturer')
            and request.user.is_lecturer()
        )


class IsStudent(permissions.BasePermission):
    """
    Permission: Only Student role can access.
    """
    
    def has_permission(self, request, view):
        return bool(
            request.user
            and hasattr(request.user, 'is_student')
            and request.user.is_student()
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission: User can access own data, or Admin can access any data.
    
    Expects view to have `get_object_user_id()` method or checks request.user.user_id.
    """
    
    def has_permission(self, request, view):
        # User must be authenticated
        return bool(request.user)
    
    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if hasattr(request.user, 'is_admin') and request.user.is_admin():
            return True
        
        # Owner check: compare user_id from URL param or object
        target_user_id = None
        
        # Try to get user_id from URL kwargs (for /api/users/{user_id}/)
        if 'user_id' in view.kwargs:
            target_user_id = int(view.kwargs['user_id'])
        # Or from object if it's a User entity
        elif hasattr(obj, 'user_id'):
            target_user_id = obj.user_id
        
        if target_user_id:
            return request.user.user_id == target_user_id
        
        return False


class IsAuthenticated(permissions.BasePermission):
    """
    Permission: Any authenticated user can access.
    """
    
    def has_permission(self, request, view):
        return bool(request.user)
