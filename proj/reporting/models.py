from django.db import models
from django.utils import timezone


class Report(models.Model):
	"""Persisted report metadata for generated exports.

	This model stores minimal metadata so the application can track
	generated reports and their exported files.
	"""
	session_id = models.IntegerField(db_index=True)
	generated_by = models.IntegerField()
	generated_date = models.DateTimeField(default=timezone.now)
	# store arbitrary metadata (statistics, session header, etc.)
	metadata = models.JSONField(null=True, blank=True)

	# export fields
	file_path = models.TextField(null=True, blank=True)
	file_type = models.CharField(max_length=20, null=True, blank=True)

	class Meta:
		db_table = "reporting_report"

	def __str__(self) -> str:  # pragma: no cover - trivial
		return f"Report {self.pk} (session={self.session_id})"
