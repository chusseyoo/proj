"""REST API Permissions for Academic Structure.

This module provides custom permission classes for role-based access control.
Follows security specifications from api_guide.md.

Roles:
- Admin: Full CRUD access (POST, PATCH, DELETE, GET)
- Lecturer: Read-only access (GET only)
- Unauthenticated: 401 Unauthorized
"""

from rest_framework import permissions


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
        
        # Check if user is staff (Django admin) or has admin role
        return request.user.is_staff or getattr(request.user, 'role', None) == 'Admin'


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
        is_admin = request.user.is_staff or getattr(request.user, 'role', None) == 'Admin'
        
        if is_admin:
            return True
        
        # Check if user is lecturer
        is_lecturer = getattr(request.user, 'role', None) == 'Lecturer'
        
        # Alternative: Check if user has LecturerProfile
        # This is safer if role field doesn't exist yet
        if not is_lecturer:
            try:
                # Check if user has related lecturer profile
                is_lecturer = hasattr(request.user, 'lecturer_profile') and request.user.lecturer_profile is not None
            except AttributeError:
                is_lecturer = False
        
        return is_lecturer


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
        is_admin = request.user.is_staff or getattr(request.user, 'role', None) == 'Admin'
        
        if is_admin:
            return True
        
        # Lecturer must be authenticated (object-level check in has_object_permission)
        is_lecturer = getattr(request.user, 'role', None) == 'Lecturer'
        
        if not is_lecturer:
            try:
                is_lecturer = hasattr(request.user, 'lecturer_profile') and request.user.lecturer_profile is not None
            except AttributeError:
                is_lecturer = False
        
        return is_lecturer
    
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
        is_admin = request.user.is_staff or getattr(request.user, 'role', None) == 'Admin'
        
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
