from django.contrib import admin
# Register your models here.
from .models import Session

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
	list_display = ('course', 'lecturer', 'date', 'start_time', 'end_time')
	search_fields = ('course__code', 'lecturer__username', 'date')

# Register your models here.
