from django.db import models

# Create your models here.
"""
Expose Program and Stream models from the DDD infrastructure layer so Django
detects them.
"""

from .infrastructure.orm.django_models import Program, Stream  # noqa: F401
