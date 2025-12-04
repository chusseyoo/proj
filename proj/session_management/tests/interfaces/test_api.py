"""API integration tests for Session Management views."""

import pytest
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from academic_structure.infrastructure.orm.django_models import Program, Course
from user_management.infrastructure.orm.django_models import User, LecturerProfile
from session_management.interfaces.api.views import _CONTAINER


@pytest.fixture(autouse=True)
def reset_container():
    """Reset the in-memory container before each test."""
    _CONTAINER['repo']._store.clear()
    _CONTAINER['repo']._next = 1
    yield
    _CONTAINER['repo']._store.clear()
    _CONTAINER['repo']._next = 1


@pytest.fixture
def api_client(db):
    return APIClient()


@pytest.fixture
def lecturer_user(db):
    user = User.objects.create_user(
        email="lecturer@example.com",
        role=User.Roles.LECTURER,
        first_name="Lect",
        last_name="User",
        password="secret123",
    )
    LecturerProfile.objects.create(user=user, department_name="Computing")
    return user


@pytest.fixture
def fk_setup(db, lecturer_user):
    program = Program.objects.create(
        program_name="Bachelor of Computer Science",
        program_code="BCS",
        department_name="Computing",
        has_streams=False,
    )
    lecturer = lecturer_user.lecturer_profile
    course = Course.objects.create(
        program=program,
        course_code="BCS012",
        course_name="Data Structures",
        department_name="Computing",
        lecturer=lecturer,
    )
    return {
        "program": program,
        "course": course,
        "lecturer": lecturer,
        "user": lecturer_user,
    }


class TestSessionAPI:
    @pytest.mark.django_db
    def test_create_session(self, api_client, fk_setup):
        user = fk_setup["user"]
        api_client.force_authenticate(user=user)

        now = timezone.now()
        payload = {
            "program_id": fk_setup["program"].program_id,
            "course_id": fk_setup["course"].course_id,
            "stream_id": None,
            "time_created": now.isoformat(),
            "time_ended": (now + timedelta(hours=1)).isoformat(),
            "latitude": "-1.28333412",
            "longitude": "36.81666588",
            "location_description": "Room A101",
        }

        url = reverse("session_management_api:session-list-create")
        resp = api_client.post(url, data=payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        body = resp.json()
        assert body["program_id"] == fk_setup["program"].program_id
        assert body["course_id"] == fk_setup["course"].course_id
        assert body["lecturer_id"] == fk_setup["lecturer"].lecturer_id
        assert body["status"] in {"created", "active", "ended"}

    @pytest.mark.django_db
    def test_list_sessions(self, api_client, fk_setup):
        user = fk_setup["user"]
        api_client.force_authenticate(user=user)

        # Create two sessions via API with non-overlapping times
        now = timezone.now()
        for i in range(2):
            payload = {
                "program_id": fk_setup["program"].program_id,
                "course_id": fk_setup["course"].course_id,
                "stream_id": None,
                # Space them out by 2 hours to avoid overlap
                "time_created": (now + timedelta(hours=i*2)).isoformat(),
                "time_ended": (now + timedelta(hours=i*2 + 1)).isoformat(),
                "latitude": "-1.28333412",
                "longitude": "36.81666588",
            }
            url = reverse("session_management_api:session-list-create")
            resp = api_client.post(url, data=payload, format="json")
            assert resp.status_code == status.HTTP_201_CREATED

        # List
        list_url = reverse("session_management_api:session-list-create")
        resp = api_client.get(list_url)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["total_count"] >= 2
        assert isinstance(data["results"], list)

    @pytest.mark.django_db
    def test_create_session_conflict(self, api_client, fk_setup):
        """Test that creating overlapping sessions returns 409 Conflict."""
        user = fk_setup["user"]
        api_client.force_authenticate(user=user)

        now = timezone.now()
        payload = {
            "program_id": fk_setup["program"].program_id,
            "course_id": fk_setup["course"].course_id,
            "stream_id": None,
            "time_created": now.isoformat(),
            "time_ended": (now + timedelta(hours=1)).isoformat(),
            "latitude": "-1.28333412",
            "longitude": "36.81666588",
        }
        url = reverse("session_management_api:session-list-create")
        
        # First creation succeeds
        resp1 = api_client.post(url, data=payload, format="json")
        assert resp1.status_code == status.HTTP_201_CREATED

        # Second creation with same times fails with Conflict
        resp2 = api_client.post(url, data=payload, format="json")
        assert resp2.status_code == status.HTTP_409_CONFLICT
        assert resp2.json()["error"]["code"] == "OverlappingSessionError"

    @pytest.mark.django_db
    def test_get_session_detail(self, api_client, fk_setup):
        user = fk_setup["user"]
        api_client.force_authenticate(user=user)

        # Create one
        now = timezone.now()
        payload = {
            "program_id": fk_setup["program"].program_id,
            "course_id": fk_setup["course"].course_id,
            "time_created": now.isoformat(),
            "time_ended": (now + timedelta(hours=1)).isoformat(),
            "latitude": "-1.28333412",
            "longitude": "36.81666588",
        }
        create_url = reverse("session_management_api:session-list-create")
        create_resp = api_client.post(create_url, data=payload, format="json")
        session_id = create_resp.json()["session_id"]

        # Get detail
        detail_url = reverse("session_management_api:session-detail", args=[session_id])
        resp = api_client.get(detail_url)
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["session_id"] == session_id
        assert body["lecturer_id"] == fk_setup["lecturer"].lecturer_id

    @pytest.mark.django_db
    def test_end_now(self, api_client, fk_setup):
        user = fk_setup["user"]
        api_client.force_authenticate(user=user)

        # Create active session
        now = timezone.now()
        payload = {
            "program_id": fk_setup["program"].program_id,
            "course_id": fk_setup["course"].course_id,
            "time_created": (now - timedelta(minutes=10)).isoformat(),
            "time_ended": (now + timedelta(minutes=50)).isoformat(),
            "latitude": "-1.28333412",
            "longitude": "36.81666588",
        }
        create_url = reverse("session_management_api:session-list-create")
        create_resp = api_client.post(create_url, data=payload, format="json")
        session_id = create_resp.json()["session_id"]

        # End now
        end_url = reverse("session_management_api:session-end-now", args=[session_id])
        resp = api_client.post(end_url)
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["session_id"] == session_id
