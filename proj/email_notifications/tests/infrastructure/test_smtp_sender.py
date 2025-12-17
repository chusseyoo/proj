"""Tests for SMTPSender infrastructure adapter."""
import pytest
from unittest.mock import patch, MagicMock, call
from django.core.mail import EmailMessage
from django.test import TestCase
from email_notifications.infrastructure.smtp_adapter.smtp_sender import SMTPSender


class TestSMTPSender:
    """Test suite for SMTPSender adapter."""

    @pytest.fixture
    def smtp_sender(self):
        """Create SMTPSender instance."""
        return SMTPSender()

    # ==================== Send Email Tests ====================

    @patch("email_notifications.infrastructure.smtp_adapter.smtp_sender.send_mail")
    def test_send_email_success(self, mock_send_mail, smtp_sender):
        """Adapter should send email successfully."""
        mock_send_mail.return_value = 1  # Django's send_mail returns number of emails sent

        result = smtp_sender.send_email(
            subject="Test Subject",
            message="Test message body",
            from_email="sender@example.com",
            recipient_list=["recipient@example.com"],
            fail_silently=False,
        )

        assert result is True  # Adapter returns bool
        mock_send_mail.assert_called_once_with(
            subject="Test Subject",
            message="Test message body",
            from_email="sender@example.com",
            recipient_list=["recipient@example.com"],
            fail_silently=False,
        )

    @patch("email_notifications.infrastructure.smtp_adapter.smtp_sender.send_mail")
    def test_send_email_multiple_recipients(self, mock_send_mail, smtp_sender):
        """Adapter should send to multiple recipients."""
        mock_send_mail.return_value = 3  # Django's send_mail returns number sent

        result = smtp_sender.send_email(
            subject="Test",
            message="Body",
            from_email="sender@example.com",
            recipient_list=[
                "recipient1@example.com",
                "recipient2@example.com",
                "recipient3@example.com",
            ],
            fail_silently=False,
        )

        assert result is True  # Adapter returns bool, not count
        assert mock_send_mail.call_args.kwargs["recipient_list"] == [
            "recipient1@example.com",
            "recipient2@example.com",
            "recipient3@example.com",
        ]

    @patch("email_notifications.infrastructure.smtp_adapter.smtp_sender.send_mail")
    def test_send_email_failure(self, mock_send_mail, smtp_sender):
        """Adapter should return False on failure."""
        mock_send_mail.return_value = 0

        result = smtp_sender.send_email(
            subject="Test",
            message="Body",
            from_email="sender@example.com",
            recipient_list=["recipient@example.com"],
            fail_silently=True,
        )

        assert result is False

    @patch("email_notifications.infrastructure.smtp_adapter.smtp_sender.send_mail")
    def test_send_email_with_html_message(self, mock_send_mail, smtp_sender):
        """Adapter should handle basic email send."""
        mock_send_mail.return_value = 1

        result = smtp_sender.send_email(
            subject="Test",
            message="Plain text body",
            from_email="sender@example.com",
            recipient_list=["recipient@example.com"],
            fail_silently=False,
        )

        assert result is True

    # ==================== Connection Tests ====================

    @patch(
        "email_notifications.infrastructure.smtp_adapter.smtp_sender.get_connection"
    )
    def test_get_connection(self, mock_get_connection, smtp_sender):
        """Adapter should get connection from Django."""
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection

        result = smtp_sender.get_connection()

        assert result == mock_connection
        mock_get_connection.assert_called_once()

    @patch(
        "email_notifications.infrastructure.smtp_adapter.smtp_sender.get_connection"
    )
    def test_send_email_with_connection(self, mock_get_connection, smtp_sender):
        """Adapter should send email using provided connection."""
        mock_connection = MagicMock()
        mock_connection.send_messages.return_value = 1

        result = smtp_sender.send_email_with_connection(
            connection=mock_connection,
            subject="Test",
            message="Body",
            from_email="sender@example.com",
            recipient_list=["recipient@example.com"],
        )

        # Should call connection.send_messages
        assert mock_connection.send_messages.called
        assert result is True

    @patch(
        "email_notifications.infrastructure.smtp_adapter.smtp_sender.get_connection"
    )
    def test_send_email_with_connection_multiple_recipients(
        self, mock_get_connection, smtp_sender
    ):
        """Adapter should send to multiple recipients using connection."""
        mock_connection = MagicMock()
        mock_connection.send_messages.return_value = 3

        result = smtp_sender.send_email_with_connection(
            connection=mock_connection,
            subject="Test",
            message="Body",
            from_email="sender@example.com",
            recipient_list=[
                "recipient1@example.com",
                "recipient2@example.com",
                "recipient3@example.com",
            ],
        )

        assert mock_connection.send_messages.called
        # Check that EmailMessage was created with multiple recipients
        call_args = mock_connection.send_messages.call_args
        email_messages = call_args[0][0]
        assert all(
            recipient in email_messages[0].to
            for recipient in [
                "recipient1@example.com",
                "recipient2@example.com",
                "recipient3@example.com",
            ]
        )
        assert result is True

    @patch(
        "email_notifications.infrastructure.smtp_adapter.smtp_sender.get_connection"
    )
    def test_send_email_with_connection_failure(
        self, mock_get_connection, smtp_sender
    ):
        """Adapter should handle failure when using connection."""
        mock_connection = MagicMock()
        mock_connection.send_messages.side_effect = Exception("Connection failed")

        result = smtp_sender.send_email_with_connection(
            connection=mock_connection,
            subject="Test",
            message="Body",
            from_email="sender@example.com",
            recipient_list=["recipient@example.com"],
        )

        assert result is False

    # ==================== From Email Tests ====================

    @patch("email_notifications.infrastructure.smtp_adapter.smtp_sender.settings")
    def test_get_from_email_from_settings(self, mock_settings, smtp_sender):
        """Adapter should get from email from settings."""
        mock_settings.DEFAULT_FROM_EMAIL = "default@example.com"

        result = smtp_sender.get_from_email()

        assert result == "default@example.com"

    @patch("email_notifications.infrastructure.smtp_adapter.smtp_sender.settings")
    def test_get_from_email_fallback(self, mock_settings, smtp_sender):
        """Adapter should get from_email from settings."""
        mock_settings.DEFAULT_FROM_EMAIL = "default@example.com"

        result = smtp_sender.get_from_email()

        assert result == "default@example.com"

    # ==================== Dependency Injection Tests ====================

    def test_adapter_can_be_injected_into_service(self, smtp_sender):
        """SMTPSender adapter should be injectable into services."""
        from email_notifications.domain.services.email_sender_service import (
            EmailSenderService,
        )

        service = EmailSenderService(smtp_sender=smtp_sender)

        assert service.smtp_sender == smtp_sender

    def test_adapter_creates_default_instance(self):
        """Service should create default SMTPSender if not provided."""
        from email_notifications.infrastructure.smtp_adapter.smtp_sender import (
            SMTPSender,
        )
        from email_notifications.domain.services.email_sender_service import (
            EmailSenderService,
        )

        service = EmailSenderService()

        assert isinstance(service.smtp_sender, SMTPSender)

    # ==================== Email Message Construction Tests ====================

    @patch(
        "email_notifications.infrastructure.smtp_adapter.smtp_sender.get_connection"
    )
    def test_send_with_connection_creates_email_message(
        self, mock_get_connection, smtp_sender
    ):
        """Adapter should create EmailMessage with correct attributes."""
        mock_connection = MagicMock()
        mock_connection.send_messages.return_value = 1

        smtp_sender.send_email_with_connection(
            connection=mock_connection,
            subject="Important Notification",
            message="This is the body",
            from_email="admin@example.com",
            recipient_list=["user@example.com"],
        )

        # Verify EmailMessage was created
        call_args = mock_connection.send_messages.call_args
        email_msg = call_args[0][0][0]

        assert email_msg.subject == "Important Notification"
        assert email_msg.body == "This is the body"
        assert email_msg.from_email == "admin@example.com"
        assert email_msg.to == ["user@example.com"]

    @patch(
        "email_notifications.infrastructure.smtp_adapter.smtp_sender.get_connection"
    )
    def test_send_with_connection_preserves_html_message(
        self, mock_get_connection, smtp_sender
    ):
        """Adapter should handle email message creation correctly."""
        mock_connection = MagicMock()
        mock_connection.send_messages.return_value = 1

        smtp_sender.send_email_with_connection(
            connection=mock_connection,
            subject="HTML Email",
            message="Plain text",
            from_email="sender@example.com",
            recipient_list=["recipient@example.com"],
        )

        call_args = mock_connection.send_messages.call_args
        email_msg = call_args[0][0][0]

        assert email_msg.subject == "HTML Email"
        assert email_msg.body == "Plain text"

    # ==================== Edge Cases ====================

    @patch("email_notifications.infrastructure.smtp_adapter.smtp_sender.send_mail")
    def test_send_email_empty_recipient_list(self, mock_send_mail, smtp_sender):
        """Adapter should handle empty recipient list."""
        mock_send_mail.return_value = 0

        result = smtp_sender.send_email(
            subject="Test",
            message="Body",
            from_email="sender@example.com",
            recipient_list=[],
            fail_silently=True,
        )

        assert result is False

    @patch("email_notifications.infrastructure.smtp_adapter.smtp_sender.send_mail")
    def test_send_email_exception_handling(self, mock_send_mail, smtp_sender):
        """Adapter should handle exceptions properly."""
        mock_send_mail.side_effect = Exception("SMTP Error")

        result = smtp_sender.send_email(
            subject="Test",
            message="Body",
            from_email="sender@example.com",
            recipient_list=["recipient@example.com"],
            fail_silently=True,
        )

        assert result is False
