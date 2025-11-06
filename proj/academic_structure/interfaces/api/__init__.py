"""REST API interface for Academic Structure bounded context.

This package provides REST API endpoints for managing:
- Programs
- Streams
- Courses

Base URL: /api/academic-structure/v1/
"""

from .views import ProgramViewSet, StreamViewSet, CourseViewSet
from .serializers import (
    ProgramSerializer,
    StreamSerializer,
    CourseSerializer,
    AssignLecturerSerializer,
    ErrorSerializer,
    PaginatedResponseSerializer
)
from .permissions import (
    IsAdminUser,
    IsLecturerOrAdmin,
    IsAssignedLecturerOrAdmin,
    ReadOnly
)

__all__ = [
    # ViewSets
    'ProgramViewSet',
    'StreamViewSet',
    'CourseViewSet',
    
    # Serializers
    'ProgramSerializer',
    'StreamSerializer',
    'CourseSerializer',
    'AssignLecturerSerializer',
    'ErrorSerializer',
    'PaginatedResponseSerializer',
    
    # Permissions
    'IsAdminUser',
    'IsLecturerOrAdmin',
    'IsAssignedLecturerOrAdmin',
    'ReadOnly',
]
