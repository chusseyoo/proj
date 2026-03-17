"""REST API Permissions for Academic Structure.

This module provides custom permission classes for role-based access control.
Follows security specifications from api_guide.md.

Roles:
- Admin: Full CRUD access (POST, PATCH, DELETE, GET)
- Lecturer: Read-only access (GET only)
- Unauthenticated: 401 Unauthorized
"""

from rest_framework import permissions


def _is_admin_user(user):
    """Support both ORM users and domain users from custom JWT auth."""
    if not user:
        return False

    is_staff = getattr(user, 'is_staff', False)
    if is_staff:
        return True

    role = getattr(user, 'role', None)
    role_value = role.value if hasattr(role, 'value') else role
    if role_value == 'Admin':
        return True

    is_admin_callable = getattr(user, 'is_admin', None)
    if callable(is_admin_callable):
        try:
            return bool(is_admin_callable())
        except TypeError:
            return False

    return False


def _is_lecturer_user(user):
    """Support both ORM users and domain users from custom JWT auth."""
    if not user:
        return False

    role = getattr(user, 'role', None)
    role_value = role.value if hasattr(role, 'value') else role
    if role_value == 'Lecturer':
        return True

    is_lecturer_callable = getattr(user, 'is_lecturer', None)
    if callable(is_lecturer_callable):
        try:
            if is_lecturer_callable():
                return True
        except TypeError:
            pass

    try:
        return hasattr(user, 'lecturer_profile') and user.lecturer_profile is not None
    except AttributeError:
        return False


class IsAdminUser(permissions.BasePermission):
    """Permission class that allows only Admin users.
    
    Used for write operations (POST, PATCH, DELETE).
    
    Admin users are identified by:
    - user.is_staff = True (Django admin access)
    - OR user.role = 'admin' (if using custom User model with role field)
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated and is an admin."""
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        return _is_admin_user(request.user)


class IsLecturerOrAdmin(permissions.BasePermission):
    """Permission class that allows Lecturers and Admins.
    
    Used for read operations (GET).
    
    Lecturers are identified by:
    - user.role = 'lecturer' (if using custom User model with role field)
    - OR existence of related LecturerProfile
    
    Admins are identified by:
    - user.is_staff = True
    - OR user.role = 'admin'
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated and is lecturer or admin."""
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user is admin
        is_admin = _is_admin_user(request.user)
        
        if is_admin:
            return True
        
        return _is_lecturer_user(request.user)


class IsAssignedLecturerOrAdmin(permissions.BasePermission):
    """Permission class for course-specific operations.
    
    Allows:
    - Admins (full access to all courses)
    - Assigned Lecturer (access only to their assigned courses)
    
    Used for operations like:
    - Creating sessions for a course
    - Viewing detailed course information
    - Managing course-specific settings
    
    Note: This permission requires object-level permission check.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated and is lecturer or admin."""
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin always has permission
        is_admin = _is_admin_user(request.user)
        
        if is_admin:
            return True
        
        # Lecturer must be authenticated (object-level check in has_object_permission)
        return _is_lecturer_user(request.user)
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission for specific course object.
        
        Args:
            request: The HTTP request
            view: The view being accessed
            obj: The course object (must have lecturer_id attribute)
        
        Returns:
            bool: True if user has permission, False otherwise
        """
        # Admin always has permission
        is_admin = _is_admin_user(request.user)
        
        if is_admin:
            return True
        
        # For lecturer, check if they are assigned to this course
        try:
            if hasattr(request.user, 'lecturer_profile'):
                lecturer_profile = request.user.lecturer_profile
                # Check if this lecturer is assigned to the course
                return obj.lecturer_id == lecturer_profile.lecturer_id
        except AttributeError:
            pass
        
        return False


class ReadOnly(permissions.BasePermission):
    """Permission class that allows only read operations.
    
    Used for public or read-only endpoints.
    Allows GET, HEAD, OPTIONS methods only.
    """
    
    def has_permission(self, request, view):
        """Allow only safe methods (GET, HEAD, OPTIONS)."""
        return request.method in permissions.SAFE_METHODS
