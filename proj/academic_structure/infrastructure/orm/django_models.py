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
