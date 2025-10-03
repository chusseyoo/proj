from django.db import models
from session.models import Session
from users.models import User

class Attendance(models.Model):
	STATUS_CHOICES = (
		('present', 'Present'),
		('absent', 'Absent'),
	)
	session = models.ForeignKey(Session, on_delete=models.CASCADE)
	student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
	timestamp = models.DateTimeField(auto_now_add=True)
	status = models.CharField(max_length=10, choices=STATUS_CHOICES)

	class Meta:
		unique_together = ('session', 'student')

	def __str__(self):
		return f"{self.student.username} - {self.session} - {self.status}"

# Create your models here.
