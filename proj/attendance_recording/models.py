"""Expose models for Django app registry.

Actual ORM implementations live under infrastructure/orm.
"""

from .infrastructure.orm.django_models import Attendance  # noqa: F401

__all__ = ["Attendance"]
