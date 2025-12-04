from django.contrib import admin
from .infrastructure.orm.django_models import Program, Course, Stream

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("program_code", "program_name", "department_name", "has_streams")
    search_fields = ("program_code", "program_name")
    list_filter = ("department_name", "has_streams")

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("course_code", "course_name", "program", "department_name", "lecturer", "is_active")
    search_fields = ("course_code", "course_name")
    list_filter = ("program", "department_name", "is_active")

@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ("stream_name", "program", "year_of_study")
    list_filter = ("program", "year_of_study")
    search_fields = ("stream_name",)
