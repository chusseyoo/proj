"""
URL Configuration for User Management API.

Routes per api_guide.md:
- POST /api/users/login
- POST /api/users/refresh
- POST /api/users/register/lecturer
- POST /api/users/register/student (admin-only)
- POST /api/users/register/admin (admin-only)
- GET/PUT/DELETE /api/users/{user_id}
- GET/PUT /api/users/{user_id}/student-profile
- GET/PUT /api/users/{user_id}/lecturer-profile
"""
from django.urls import path

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

app_name = 'user_management'

urlpatterns = [
    # Auth endpoints
    path('login', LoginView.as_view(), name='login'),
    path('refresh', RefreshTokenView.as_view(), name='refresh'),
    
    # Registration endpoints
    path('register/lecturer', RegisterLecturerView.as_view(), name='register-lecturer'),
    path('register/student', RegisterStudentView.as_view(), name='register-student'),
    path('register/admin', RegisterAdminView.as_view(), name='register-admin'),
    
    # User management endpoints
    path('<int:user_id>', UserDetailView.as_view(), name='user-detail'),
    
    # Profile endpoints (nested under user)
    path('<int:user_id>/student-profile', StudentProfileView.as_view(), name='student-profile'),
    path('<int:user_id>/lecturer-profile', LecturerProfileView.as_view(), name='lecturer-profile'),
]
