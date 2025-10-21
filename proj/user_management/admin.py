from django.contrib import admin

from .infrastructure.orm.django_models import (
	User,
	StudentProfile,
	LecturerProfile,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
	list_display = ("user_id", "email", "first_name", "last_name", "role", "is_active")
	list_filter = ("role", "is_active")
	search_fields = ("email", "first_name", "last_name")
	ordering = ("email",)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
	list_display = ("student_profile_id", "student_id", "user", "program", "stream", "year_of_study")
	search_fields = ("student_id", "user__email", "user__first_name", "user__last_name")
	list_filter = ("program", "stream", "year_of_study")


@admin.register(LecturerProfile)
class LecturerProfileAdmin(admin.ModelAdmin):
	list_display = ("lecturer_id", "user", "department_name")
	search_fields = ("user__email", "user__first_name", "user__last_name", "department_name")
