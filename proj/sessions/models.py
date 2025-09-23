from django.db import models
from courses.models import Course
from users.models import User

class Session(models.Model):
	course = models.ForeignKey(Course, on_delete=models.CASCADE)
	lecturer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'lecturer'})
	date = models.DateField()
	start_time = models.TimeField()
	end_time = models.TimeField()

	def __str__(self):
		return f"{self.course.code} - {self.date} ({self.start_time}-{self.end_time})"

# Create your models here.
