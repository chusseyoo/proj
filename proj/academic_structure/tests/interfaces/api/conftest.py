"""Shared fixtures for API tests."""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def admin_user(db):
    """Admin user for testing."""
    return User.objects.create_user(
        email='admin@test.com',
        role='Admin',
        first_name='Admin',
        last_name='User',
        password='testpass123',
        is_staff=True
    )


@pytest.fixture
def lecturer_user(db):
    """Lecturer user for testing."""
    return User.objects.create_user(
        email='lecturer@test.com',
        role='Lecturer',
        first_name='John',
        last_name='Doe',
        password='testpass123'
    )


@pytest.fixture
def student_user(db):
    """Student user for testing."""
    return User.objects.create_user(
        email='student@test.com',
        role='Student',
        first_name='Jane',
        last_name='Smith',
        password=None
    )
