"""
Expose models for the user_management app so Django can discover them.
Actual model implementations live under infrastructure/orm/django_models.py
as per the DDD folder structure.
"""

# Import models so Django detects them during app loading
from .infrastructure.orm.django_models import (  # noqa: F401
	User,
	StudentProfile,
	LecturerProfile,
)
