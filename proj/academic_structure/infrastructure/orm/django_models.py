from __future__ import annotations

from django.db import models


class Program(models.Model):
    program_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    has_streams = models.BooleanField(default=False)

    class Meta:
        db_table = "programs"
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Stream(models.Model):
    stream_id = models.AutoField(primary_key=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="streams")
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "streams"
        ordering = ["name"]
        unique_together = ("program", "name")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.program.name} - {self.name}"


class Course(models.Model):
    """Course belonging to a Program. Minimal implementation to support Session targeting.

    Note: lecturer is a LecturerProfile (one-to-one with User) kept as a FK to
    `user_management.LecturerProfile` to allow permission/assignment checks.
    """

    course_id = models.AutoField(primary_key=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="courses")
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    lecturer = models.ForeignKey(
        "user_management.LecturerProfile",
        on_delete=models.PROTECT,
        related_name="courses",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "courses"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["program"], name="idx_courses_program"),
            models.Index(fields=["lecturer"], name="idx_courses_lecturer"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.code} - {self.name}"
