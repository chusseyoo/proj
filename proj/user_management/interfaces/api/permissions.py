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
    
    Checks URL kwargs for user_id and verifies ownership or admin role.
    """
    
    def has_permission(self, request, view):
        # User must be authenticated and have user_id attribute
        if not request.user or not hasattr(request.user, 'user_id'):
            return False
        
        # Admin can access everything
        if hasattr(request.user, 'is_admin') and request.user.is_admin():
            return True
        
        # Get target user_id from URL kwargs
        target_user_id = view.kwargs.get('user_id')
        if target_user_id:
            # User can only access own data
            return request.user.user_id == int(target_user_id)
        
        # If no user_id in URL, allow (let view handle it)
        return True


class IsAuthenticated(permissions.BasePermission):
    """
    Permission: Any authenticated user can access.
    """
    
    def has_permission(self, request, view):
        return bool(request.user)
