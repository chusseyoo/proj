from django.contrib import admin

# Register your models here.
from .models import ReportExport

@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
	list_display = ('id', 'created_at', 'file', 'description')
