"""
URL configuration for proj project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='lecturer-login', permanent=False)),
    path('student/scan', TemplateView.as_view(template_name='student-qr-scan.html'), name='student-qr-scan'),
    path('lecturer/login', TemplateView.as_view(template_name='lecturer-login.html'), name='lecturer-login'),
    path('lecturer/register', TemplateView.as_view(template_name='lecturer-register.html'), name='lecturer-register'),
    path('lecturer/dashboard', TemplateView.as_view(template_name='lecturer-dashboard.html'), name='lecturer-dashboard'),
    path('lecturer/courses', TemplateView.as_view(template_name='lecturer-courses.html'), name='lecturer-courses'),
    path('lecturer/courses/add', TemplateView.as_view(template_name='lecturer-add-course.html'), name='lecturer-add-course'),
    path('lecturer/sessions/create', TemplateView.as_view(template_name='lecturer-create-session.html'), name='lecturer-create-session'),
    path('lecturer/reports', TemplateView.as_view(template_name='lecturer-reports.html'), name='lecturer-reports'),
    path('admin/', admin.site.urls),
    path('api/users/', include('user_management.interfaces.api.urls')),
    path('api/academic-structure/v1/', include('academic_structure.interfaces.api.urls')),
    path('api/session-management/v1/', include('session_management.interfaces.api.urls')),
    path('', include('attendance_recording.urls')),
    path('api/email-notifications/v1/', include('email_notifications.interfaces.api.urls')),
]

if settings.DEBUG:
    if hasattr(settings, 'MEDIA_URL') and settings.MEDIA_URL:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if hasattr(settings, 'STATIC_URL') and settings.STATIC_URL:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)