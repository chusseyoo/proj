import pytest


@pytest.mark.django_db
def test_admin_retry_failed(authenticated_admin_client, en_session, en_student_profiles, make_notifications):
    # Create 3 notifications: failed, sent, pending
    notifs = make_notifications(
        session=en_session,
        students=en_student_profiles[:3],
        statuses=["failed", "sent", "pending"],
    )
    ids = [n.email_id for n in notifs]

    url = "/api/email-notifications/v1/admin/notifications/retry"
    resp = authenticated_admin_client.post(url, data={"email_ids": ids}, format="json")

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["retried"] == 1  # only the failed one
    assert data["skipped"] >= 2  # sent and pending skipped


@pytest.mark.django_db
def test_admin_retry_requires_admin(api_client, en_session, en_student_profiles, make_notifications):
    notifs = make_notifications(en_session, en_student_profiles[:2], ["failed", "failed"])
    url = "/api/email-notifications/v1/admin/notifications/retry"
    resp = api_client.post(url, data={"email_ids": [n.email_id for n in notifs]}, format="json")
    assert resp.status_code in (401, 403)
