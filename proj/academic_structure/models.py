from django.db import models

# Create your models here.
"""
Expose Program, Stream, and Course models from the DDD infrastructure layer so Django
detects them.
"""

from .infrastructure.orm.django_models import Program, Stream, Course  # noqa: F401
