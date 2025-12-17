"""Pytest configuration for email_notifications tests."""
import pytest
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def jwt_secret():
    """JWT secret key for testing."""
    return "test-secret-key-for-jwt-token-generation"

