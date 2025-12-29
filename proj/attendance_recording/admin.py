from django.contrib import admin

from .infrastructure.orm.django_models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
	list_display = (
		"attendance_id",
		"student_profile",
		"session",
		"status",
		"is_within_radius",
		"time_recorded",
		"latitude",
		"longitude",
	)
	list_filter = (
		"status",
		"is_within_radius",
		"session",
		"student_profile",
		"time_recorded",
	)
	search_fields = (
		"student_profile__student_id",
		"student_profile__user__email",
		"session__session_id",
		"session__course__course_code",
	)
	ordering = ("-time_recorded",)

	def get_readonly_fields(self, request, obj=None):
		return [field.name for field in self.model._meta.fields]

	def has_add_permission(self, request):
		return False

	def has_change_permission(self, request, obj=None):
		# Attendance records are immutable per domain rules
		return False

	def has_delete_permission(self, request, obj=None):
		return False
