import pytest


@pytest.mark.django_db
def test_list_notifications_as_owner(authenticated_lecturer_client, en_lecturer_user_with_profile, en_session, en_student_profiles, make_notifications):
    # Ensure lecturer client is the owner (session created with lecturer_user_with_profile fixture)
    make_notifications(en_session, en_student_profiles[:2], ["sent", "failed"])

    url = f"/api/email-notifications/v1/sessions/{en_session.session_id}/notifications"
    resp = authenticated_lecturer_client.get(url)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_count"] == 2
    assert {r["status"] for r in body["results"]} == {"sent", "failed"}


@pytest.mark.django_db
def test_list_notifications_as_admin(authenticated_admin_client, en_session, en_student_profiles, make_notifications):
    make_notifications(en_session, en_student_profiles[:3], ["pending", "sent", "failed"])
    url = f"/api/email-notifications/v1/sessions/{en_session.session_id}/notifications?status=sent"
    resp = authenticated_admin_client.get(url)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_count"] == 1
    assert body["results"][0]["status"] == "sent"


@pytest.mark.django_db
def test_list_notifications_forbidden_for_non_owner(api_client, en_another_lecturer_with_profile, en_session):
    # Authenticate as another lecturer
    from rest_framework.test import APIClient
    from user_management.application.services.authentication_service import AuthenticationService
    from user_management.application.services.password_service import PasswordService
    from user_management.infrastructure.repositories.user_repository import UserRepository
    from user_management.infrastructure.repositories.student_profile_repository import StudentProfileRepository

    client = APIClient()
    user_repo = UserRepository()
    auth_service = AuthenticationService(user_repository=user_repo, password_service=PasswordService(user_repo), student_repository=StudentProfileRepository())
    tokens = auth_service.login(email="other.lecturer@example.com", password="LecturerPass123!")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")

    url = f"/api/email-notifications/v1/sessions/{en_session.session_id}/notifications"
    resp = client.get(url)
    assert resp.status_code == 403
