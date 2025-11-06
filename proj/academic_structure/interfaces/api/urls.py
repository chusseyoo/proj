"""URL Configuration for Academic Structure API.

This module defines URL routing for the REST API endpoints.
Base path: /api/academic-structure/v1/

Follows routing specifications from api_guide.md.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views import ProgramViewSet, StreamViewSet, CourseViewSet


# Create main router
router = DefaultRouter()

# Register Program routes
# Generates:
# - GET    /programs/
# - POST   /programs/
# - GET    /programs/{id}/
# - PATCH  /programs/{id}/
# - DELETE /programs/{id}/
router.register(r'programs', ProgramViewSet, basename='program')

# Register Course routes
# Generates:
# - GET    /courses/
# - POST   /courses/
# - GET    /courses/{id}/
# - PATCH  /courses/{id}/
# - DELETE /courses/{id}/
router.register(r'courses', CourseViewSet, basename='course')

# Register Stream routes (standalone)
# Generates:
# - GET    /streams/{id}/
# - PATCH  /streams/{id}/
# - DELETE /streams/{id}/
router.register(r'streams', StreamViewSet, basename='stream')

# Create nested router for streams under programs
# Generates:
# - GET    /programs/{program_pk}/streams/
# - POST   /programs/{program_pk}/streams/
programs_router = routers.NestedDefaultRouter(router, r'programs', lookup='program')
programs_router.register(r'streams', StreamViewSet, basename='program-streams')

# URL patterns
urlpatterns = [
    # Include main router
    path('', include(router.urls)),
    
    # Include nested router for streams
    path('', include(programs_router.urls)),
]

# URL patterns summary:
# Programs:
#   GET    /api/academic-structure/v1/programs/
#   POST   /api/academic-structure/v1/programs/
#   GET    /api/academic-structure/v1/programs/{id}/
#   GET    /api/academic-structure/v1/programs/by-code/{code}/
#   PATCH  /api/academic-structure/v1/programs/{id}/
#   DELETE /api/academic-structure/v1/programs/{id}/
#
# Streams (nested under programs):
#   GET    /api/academic-structure/v1/programs/{program_id}/streams/
#   POST   /api/academic-structure/v1/programs/{program_id}/streams/
#
# Streams (standalone):
#   GET    /api/academic-structure/v1/streams/{id}/
#   PATCH  /api/academic-structure/v1/streams/{id}/
#   DELETE /api/academic-structure/v1/streams/{id}/
#
# Courses:
#   GET    /api/academic-structure/v1/courses/
#   POST   /api/academic-structure/v1/courses/
#   GET    /api/academic-structure/v1/courses/{id}/
#   GET    /api/academic-structure/v1/courses/by-code/{code}/
#   PATCH  /api/academic-structure/v1/courses/{id}/
#   DELETE /api/academic-structure/v1/courses/{id}/
#   POST   /api/academic-structure/v1/courses/{id}/assign-lecturer/
#   POST   /api/academic-structure/v1/courses/{id}/unassign-lecturer/
