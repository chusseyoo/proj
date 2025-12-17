import pytest


@pytest.mark.django_db
def test_statistics_admin_only(authenticated_admin_client, api_client, en_session, en_student_profiles, make_notifications):
    # Create data
    make_notifications(en_session, en_student_profiles[:3], ["sent", "failed", "pending"])

    url = "/api/email-notifications/v1/admin/notifications/statistics"

    # Admin can access
    resp_admin = authenticated_admin_client.get(url)
    assert resp_admin.status_code == 200
    data = resp_admin.json()
    assert set(["total", "sent", "failed", "pending", "success_rate"]) <= set(data.keys())

    # Unauthenticated blocked
    resp_unauth = api_client.get(url)
    assert resp_unauth.status_code in (401, 403)
