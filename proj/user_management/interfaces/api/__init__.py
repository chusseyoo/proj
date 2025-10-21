"""
User Management API Interface Layer.

Provides REST API endpoints, JWT authentication, role-based permissions,
and exception handling for the user management bounded context.
"""

from .views import (
    LoginView,
    RefreshTokenView,
    RegisterLecturerView,
    RegisterStudentView,
    RegisterAdminView,
    UserDetailView,
    StudentProfileView,
    LecturerProfileView,
)

__all__ = [
    'LoginView',
    'RefreshTokenView',
    'RegisterLecturerView',
    'RegisterStudentView',
    'RegisterAdminView',
    'UserDetailView',
    'StudentProfileView',
    'LecturerProfileView',
]
