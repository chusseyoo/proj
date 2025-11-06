from __future__ import annotations

from django.db import models
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    RegexValidator,
    MinLengthValidator,
    MaxLengthValidator,
)


class Program(models.Model):
    program_id = models.AutoField(primary_key=True)
    program_name = models.CharField(max_length=200, unique=True, validators=[MinLengthValidator(5)])
    program_code = models.CharField(
        max_length=3,
        unique=True,
        validators=[RegexValidator(regex=r"^[A-Z]{3}$", message="Program code must be 3 uppercase letters")],
    )
    department_name = models.CharField(max_length=50, validators=[MinLengthValidator(5), MaxLengthValidator(50)])
    has_streams = models.BooleanField(default=False)

    class Meta:
        app_label = "academic_structure"
        db_table = "programs"
        ordering = ["program_name"]
        indexes = [
            models.Index(fields=["program_code"], name="idx_programs_program_code"),
            models.Index(fields=["department_name"], name="idx_programs_department"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.program_code} - {self.program_name}"

    def clean(self):
        # Normalize program_code to uppercase
        if self.program_code:
            self.program_code = self.program_code.strip().upper()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Stream(models.Model):
    stream_id = models.AutoField(primary_key=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="streams")
    stream_name = models.CharField(max_length=100, validators=[MinLengthValidator(2)])
    year_of_study = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])

    class Meta:
        app_label = "academic_structure"
        db_table = "streams"
        ordering = ["program_id", "year_of_study", "stream_name"]
        unique_together = ("program", "stream_name", "year_of_study")
        indexes = [
            models.Index(fields=["program"], name="idx_streams_program_id"),
            models.Index(fields=["year_of_study"], name="idx_streams_year"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.program.program_code} Year {self.year_of_study} - {self.stream_name}"

    def clean(self):
        # Ensure program has streams enabled
        if self.program and not self.program.has_streams:
            from django.core.exceptions import ValidationError as DJValidationError

            raise DJValidationError("Cannot create stream for program that does not have streams enabled")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Course(models.Model):
    """Course belonging to a Program.

    Lecturer is nullable and uses SET_NULL on delete. Course code is validated and
    normalized to uppercase on save.
    """

    course_id = models.AutoField(primary_key=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="courses")
    course_code = models.CharField(
        max_length=6,
        unique=True,
        validators=[RegexValidator(regex=r"^[A-Z0-9]{6}$", message="Course code must be exactly 6 uppercase alphanumeric characters (e.g., BCS012, BEG230, DIT410)")],
    )
    course_name = models.CharField(max_length=200, validators=[MinLengthValidator(3)])
    department_name = models.CharField(max_length=50, validators=[MinLengthValidator(5), MaxLengthValidator(50)])
    lecturer = models.ForeignKey(
        "user_management.LecturerProfile",
        on_delete=models.SET_NULL,
        related_name="courses",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "academic_structure"
        db_table = "courses"
        ordering = ["course_code"]
        indexes = [
            models.Index(fields=["program"], name="idx_courses_program"),
            models.Index(fields=["lecturer"], name="idx_courses_lecturer"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.course_code} - {self.course_name}"

    def clean(self):
        # Normalize course_code to uppercase
        if self.course_code:
            self.course_code = self.course_code.strip().upper()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
