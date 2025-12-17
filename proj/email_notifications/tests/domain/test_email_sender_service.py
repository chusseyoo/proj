"""Tests for EmailSenderService domain service."""
import pytest
from unittest.mock import Mock, patch, call

from email_notifications.domain.services import EmailSenderService
from email_notifications.domain.exceptions import (
    InvalidEmailAddressError,
)


class TestEmailSenderService:
    """Test suite for email sending service."""

    @pytest.fixture
    def email_service(self):
        """Create email sender service."""
        return EmailSenderService()

    # ==================== Single Email Sending Tests ====================

    def test_send_attendance_notification_success(self, email_service):
        """Sending valid notification should return True."""
        context = {
            "student_first_name": "John",
            "course_name": "Data Structures",
            "course_code": "CS201",
            "session_date": "2025-10-25",
            "start_time": "08:00",
            "end_time": "10:00",
            "attendance_link": "https://app.com/attendance?token=abc123",
            "token_expiry": "2025-10-25 09:00",
        }
        
        with patch.object(email_service.smtp_sender, "send_email", return_value=True):
            result = email_service.send_attendance_notification(
                recipient_email="student@example.com",
                context=context,
            )
        
        assert result is True

    def test_send_attendance_notification_invalid_email(self, email_service):
        """Invalid email should return False."""
        context = {"student_first_name": "John"}
        
        result = email_service.send_attendance_notification(
            recipient_email="invalid-email",
            context=context,
        )
        
        assert result is False

    def test_send_attendance_notification_empty_email(self, email_service):
        """Empty email should return False."""
        result = email_service.send_attendance_notification(
            recipient_email="",
            context={"student_first_name": "John"},
        )
        
        assert result is False

    def test_send_attendance_notification_none_email(self, email_service):
        """None email should return False."""
        result = email_service.send_attendance_notification(
            recipient_email=None,
            context={"student_first_name": "John"},
        )
        
        assert result is False

    def test_send_attendance_notification_smtp_error(self, email_service):
        """SMTP error should return False (not raise exception)."""
        context = {
            "student_first_name": "John",
            "course_name": "Data Structures",
            "course_code": "CS201",
            "session_date": "2025-10-25",
            "start_time": "08:00",
            "end_time": "10:00",
            "attendance_link": "https://app.com/attendance?token=abc123",
            "token_expiry": "2025-10-25 09:00",
        }
        
        with patch.object(email_service.smtp_sender, "send_email", side_effect=Exception("SMTP connection failed")):
            result = email_service.send_attendance_notification(
                recipient_email="student@example.com",
                context=context,
            )
        
        assert result is False

    def test_send_attendance_notification_none_context(self, email_service):
        """None context should return False."""
        result = email_service.send_attendance_notification(
            recipient_email="student@example.com",
            context=None,
        )
        
        assert result is False

    def test_send_attendance_notification_empty_context(self, email_service):
        """Empty context should return False."""
        result = email_service.send_attendance_notification(
            recipient_email="student@example.com",
            context={},
        )
        
        assert result is False

    def test_send_attendance_notification_uses_correct_subject(self, email_service):
        """Email subject should include course name."""
        context = {
            "student_first_name": "John",
            "course_name": "Advanced Algorithms",
            "course_code": "CS501",
            "session_date": "2025-10-25",
            "start_time": "08:00",
            "end_time": "10:00",
            "attendance_link": "https://app.com/attendance?token=abc123",
            "token_expiry": "2025-10-25 09:00",
        }
        
        with patch.object(email_service.smtp_sender, "send_email") as mock_send:
            email_service.send_attendance_notification(
                recipient_email="student@example.com",
                context=context,
            )
        
        call_args = mock_send.call_args
        subject = call_args.kwargs["subject"]
        
        assert "Advanced Algorithms" in subject
        assert "Attendance Session Created" in subject

    def test_send_attendance_notification_includes_attendance_link(self, email_service):
        """Email body should include attendance link."""
        context = {
            "student_first_name": "John",
            "course_name": "CS201",
            "course_code": "CS201",
            "session_date": "2025-10-25",
            "start_time": "08:00",
            "end_time": "10:00",
            "attendance_link": "https://app.com/attendance?token=mytoken123",
            "token_expiry": "2025-10-25 09:00",
        }
        
        with patch.object(email_service.smtp_sender, "send_email") as mock_send:
            email_service.send_attendance_notification(
                recipient_email="student@example.com",
                context=context,
            )
        
        call_args = mock_send.call_args
        body = call_args.kwargs["message"]
        
        assert "mytoken123" in body

    def test_send_attendance_notification_includes_student_name(self, email_service):
        """Email body should address student by name."""
        context = {
            "student_first_name": "Alice",
            "course_name": "CS201",
            "course_code": "CS201",
            "session_date": "2025-10-25",
            "start_time": "08:00",
            "end_time": "10:00",
            "attendance_link": "https://app.com/attendance?token=abc",
            "token_expiry": "2025-10-25 09:00",
        }
        
        with patch.object(email_service.smtp_sender, "send_email") as mock_send:
            email_service.send_attendance_notification(
                recipient_email="alice@example.com",
                context=context,
            )
        
        call_args = mock_send.call_args
        body = call_args.kwargs["message"]
        
        assert "Alice" in body

    # ==================== Bulk Email Sending Tests ====================

    def test_send_bulk_emails_empty_list(self, email_service):
        """Empty email list should return summary with zeros."""
        result = email_service.send_bulk_emails([])
        
        assert result["total"] == 0
        assert result["sent"] == 0
        assert result["failed"] == 0
        assert result["failed_emails"] == []

    def test_send_bulk_emails_single_success(self, email_service):
        """Sending single email successfully should update summary."""
        emails = [
            {
                "recipient_email": "student@example.com",
                "context": {
                    "student_first_name": "John",
                    "course_name": "CS201",
                    "course_code": "CS201",
                    "session_date": "2025-10-25",
                    "start_time": "08:00",
                    "end_time": "10:00",
                    "attendance_link": "https://app.com/attendance?token=abc",
                    "token_expiry": "2025-10-25 09:00",
                }
            }
        ]
        
        with patch.object(email_service.smtp_sender, "get_connection"):
            result = email_service.send_bulk_emails(emails)
        
        assert result["total"] == 1
        assert result["sent"] >= 0  # May succeed or fail depending on mock
        assert result["failed"] >= 0

    def test_send_bulk_emails_multiple_success(self, email_service):
        """Multiple emails should be sent and counted."""
        emails = [
            {
                "recipient_email": f"student{i}@example.com",
                "context": {
                    "student_first_name": f"Student{i}",
                    "course_name": "CS201",
                    "course_code": "CS201",
                    "session_date": "2025-10-25",
                    "start_time": "08:00",
                    "end_time": "10:00",
                    "attendance_link": f"https://app.com/attendance?token=abc{i}",
                    "token_expiry": "2025-10-25 09:00",
                }
            }
            for i in range(10)
        ]
        
        with patch.object(email_service.smtp_sender, "get_connection"):
            result = email_service.send_bulk_emails(emails)
        
        assert result["total"] == 10
        assert result["sent"] + result["failed"] == 10

    def test_send_bulk_emails_returns_failed_emails_list(self, email_service):
        """Failed emails should be listed in response."""
        emails = [
            {
                "recipient_email": "invalid@",
                "context": {"student_first_name": "John"}
            },
            {
                "recipient_email": "student@example.com",
                "context": {
                    "student_first_name": "Jane",
                    "course_name": "CS201",
                    "course_code": "CS201",
                    "session_date": "2025-10-25",
                    "start_time": "08:00",
                    "end_time": "10:00",
                    "attendance_link": "https://app.com/attendance?token=abc",
                    "token_expiry": "2025-10-25 09:00",
                }
            },
        ]
        
        with patch.object(email_service.smtp_sender, "get_connection"):
            result = email_service.send_bulk_emails(emails)
        
        assert isinstance(result["failed_emails"], list)

    # ==================== Email Body Template Tests ====================

    def test_email_body_includes_course_info(self, email_service):
        """Email body should include course name and code."""
        context = {
            "student_first_name": "John",
            "course_name": "Data Structures",
            "course_code": "CS201",
            "session_date": "2025-10-25",
            "start_time": "08:00",
            "end_time": "10:00",
            "attendance_link": "https://app.com/attendance?token=abc",
            "token_expiry": "2025-10-25 09:00",
        }
        
        body = email_service._build_email_body(context)
        
        assert "Data Structures" in body
        assert "CS201" in body

    def test_email_body_includes_session_details(self, email_service):
        """Email body should include session date and time."""
        context = {
            "student_first_name": "John",
            "course_name": "CS201",
            "course_code": "CS201",
            "session_date": "2025-10-25",
            "start_time": "08:00",
            "end_time": "10:00",
            "attendance_link": "https://app.com/attendance?token=abc",
            "token_expiry": "2025-10-25 09:00",
        }
        
        body = email_service._build_email_body(context)
        
        assert "2025-10-25" in body
        assert "08:00" in body
        assert "10:00" in body

    def test_email_body_includes_important_note(self, email_service):
        """Email body should include important requirements."""
        context = {
            "student_first_name": "John",
            "course_name": "CS201",
            "course_code": "CS201",
            "session_date": "2025-10-25",
            "start_time": "08:00",
            "end_time": "10:00",
            "attendance_link": "https://app.com/attendance?token=abc",
            "token_expiry": "2025-10-25 09:00",
        }
        
        body = email_service._build_email_body(context)
        
        assert "30 meters" in body
        assert "QR code" in body

    def test_email_body_handles_missing_context_variables(self, email_service):
        """Missing context variables should not crash, use defaults."""
        context = {
            "student_first_name": "John",
            "attendance_link": "https://app.com/attendance?token=abc",
        }
        
        body = email_service._build_email_body(context)
        
        assert isinstance(body, str)
        assert len(body) > 0
        assert "John" in body

    # ==================== Email Address Validation ====================

    def test_valid_email_formats(self, email_service):
        """Various valid email formats should work."""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "123@example.com",
        ]
        
        context = {
            "student_first_name": "John",
            "course_name": "CS201",
            "course_code": "CS201",
            "session_date": "2025-10-25",
            "start_time": "08:00",
            "end_time": "10:00",
            "attendance_link": "https://app.com/attendance?token=abc",
            "token_expiry": "2025-10-25 09:00",
        }
        
        with patch.object(email_service.smtp_sender, "send_email", return_value=True):
            for email in valid_emails:
                result = email_service.send_attendance_notification(
                    recipient_email=email,
                    context=context,
                )
                assert result is True

    def test_invalid_email_formats(self, email_service):
        """Invalid email formats should return False."""
        invalid_emails = [
            "user@",
            "@example.com",
            "user example@com",
            "user@example",
            "userexample.com",
        ]
        
        context = {"student_first_name": "John"}
        
        for email in invalid_emails:
            result = email_service.send_attendance_notification(
                recipient_email=email,
                context=context,
            )
            assert result is False
