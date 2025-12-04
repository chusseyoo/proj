
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client

User = get_user_model()

@pytest.mark.django_db
def test_admin_pages_accessible(client):
    # Create superuser
    admin_user = User.objects.create_superuser(
        email="admin@example.com",
        password="password123",
        first_name="Admin",
        last_name="User",
        role="Admin"
    )
    
    client.force_login(admin_user)
    
    # List of admin changelist URLs to check
    # Format: 'admin:<app_label>_<model_name>_changelist'
    pages = [
        'admin:academic_structure_program_changelist',
        'admin:academic_structure_course_changelist',
        'admin:academic_structure_stream_changelist',
        'admin:session_management_session_changelist',
    ]
    
    for page in pages:
        url = reverse(page)
        response = client.get(url)
        assert response.status_code == 200, f"Failed to access {page}"
