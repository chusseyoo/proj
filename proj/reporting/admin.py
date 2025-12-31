from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
	"""Admin interface for Report model.
	
	Reports track generated attendance reports with optional file exports.
	- View-only reports (file_path/file_type NULL)
	- Exported reports (file_path and file_type set)
	"""
	list_display = (
		"id",
		"session_id",
		"generated_by",
		"generated_date",
		"export_status_display",
		"file_type",
	)
	list_filter = ("generated_date", "file_type")
	search_fields = (
		"id",
		"session_id",
		"generated_by",
	)
	ordering = ("-generated_date",)
	readonly_fields = ("id", "generated_date", "session_id", "generated_by", "file_path", "file_type", "metadata")

	def export_status_display(self, obj):
		"""Display export status (exported or not_exported) based on file_path presence."""
		return "exported" if obj.file_path else "not_exported"

	export_status_display.short_description = "Export Status"

	def has_add_permission(self, request):
		"""Reports are only created via API layer, not manually in admin."""
		return False

	def has_delete_permission(self, request, obj=None):
		"""Allow admin to delete old/test reports for cleanup."""
		return request.user.is_staff

	def has_change_permission(self, request, obj=None):
		"""Reports are immutable after creation (per domain rules)."""
		return False


