from django.db import models

class ReportExport(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	file = models.FileField(upload_to='reports/')
	description = models.CharField(max_length=255, blank=True)

	def __str__(self):
		return f"Report {self.id} - {self.created_at}"

# Create your models here.
