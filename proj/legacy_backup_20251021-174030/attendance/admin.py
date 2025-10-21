from django.contrib import admin
# Register your models here.
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
	list_display = ('session', 'student', 'timestamp', 'status')
	search_fields = ('session__course__code', 'student__username', 'status')

# Register your models here.
