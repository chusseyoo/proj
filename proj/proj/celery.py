"""Celery application bootstrap for the Django project."""

from __future__ import annotations

import os

from celery import Celery

# Default Django settings module for the celery command.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proj.settings")

app = Celery("proj")

# Load all CELERY_* settings from Django settings.py.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover task modules from all installed Django apps.
app.autodiscover_tasks()
