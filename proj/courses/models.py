from django.db import models
from users.models import User

class Course(models.Model):
	name = models.CharField(max_length=100)
	code = models.CharField(max_length=20, unique=True)
	lecturer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'lecturer'})

	def __str__(self):
		return f"{self.code} - {self.name}"

# Create your models here.
