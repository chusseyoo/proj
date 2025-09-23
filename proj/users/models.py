from django.db import models
from django.contrib.auth.models import AbstractUser, Group

class User(AbstractUser):
	ROLE_CHOICES = (
		('admin', 'Admin'),
		('lecturer', 'Lecturer'),
		('student', 'Student'),
	)
	role = models.CharField(max_length=10, choices=ROLE_CHOICES)
	qr_code = models.CharField(max_length=255, blank=True, null=True, unique=True)

	def __str__(self):
		return f"{self.username} ({self.role})"

# Create your models here.
