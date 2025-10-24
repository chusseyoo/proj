"""Admin helper views for the reporting context (scaffold)."""
from django.contrib import admin


# Placeholder: register a lightweight admin if a Report model exists
try:
    from reporting.models import Report  # type: ignore

    @admin.register(Report)
    class ReportAdmin(admin.ModelAdmin):
        list_display = ("id", "session", "generated_by", "generated_date", "file_type")
        readonly_fields = ("generated_date",)
except Exception:  # pragma: no cover - models may not exist yet
    # No-op placeholder for scaffolding
    pass
