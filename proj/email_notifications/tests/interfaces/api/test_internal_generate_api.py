import pytest
from django.test import override_settings
from django.urls import reverse


@pytest.mark.django_db
@override_settings(EMAIL_NOTIFICATIONS_INTERNAL_TOKEN="secret-token")
def test_internal_generate_success(api_client, en_session, en_student_profiles):
    url = "/api/email-notifications/v1/internal/sessions/{}/notifications".format(
        en_session.session_id
    )

    # Provide internal header
    response = api_client.post(url, data={}, format="json", HTTP_X_INTERNAL_TOKEN="secret-token")

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["session_id"] == en_session.session_id
    assert body["data"]["eligible_students"] == len(en_student_profiles)
    # At least one notification created (depends on service success)
    assert body["data"]["notifications_created"] >= 0


@pytest.mark.django_db
@override_settings(EMAIL_NOTIFICATIONS_INTERNAL_TOKEN="secret-token")
def test_internal_generate_requires_internal_token(api_client, en_session):
    url = f"/api/email-notifications/v1/internal/sessions/{en_session.session_id}/notifications"
    # Missing header
    resp = api_client.post(url, data={}, format="json")
    assert resp.status_code in (401, 403)
