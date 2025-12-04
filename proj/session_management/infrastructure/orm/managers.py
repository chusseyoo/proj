from __future__ import annotations

from django.db import models
from django.utils import timezone
from typing import Optional


class SessionQuerySet(models.QuerySet):
    def active(self, now: Optional[models.DateTimeField] = None):
        if now is None:
            now = timezone.now()
        return self.filter(time_created__lte=now, time_ended__gt=now)

    def overlapping(self, lecturer_id: int, start, end):
        """Return queryset of sessions overlapping given time window for lecturer."""
        return self.filter(
            lecturer_id=lecturer_id,
            time_created__lt=end,
            time_ended__gt=start,
        )


class SessionManager(models.Manager):
    """Manager exposing convenience helpers used by services and repos."""

    def get_queryset(self):
        return SessionQuerySet(self.model, using=self._db)

    def active(self, now: Optional[models.DateTimeField] = None):
        return self.get_queryset().active(now)

    def overlapping_exists(self, lecturer_id: int, start, end) -> bool:
        return self.get_queryset().overlapping(lecturer_id, start, end).exists()
