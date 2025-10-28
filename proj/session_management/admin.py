from django.contrib import admin

from .models import Session


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
	list_display = ("session_id", "program", "course", "lecturer", "time_created", "time_ended")
	search_fields = ("lecturer__user__email", "course__code")

