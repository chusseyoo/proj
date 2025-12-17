"""Email sending service via SMTP adapter."""
from typing import List, Dict, Any, Optional

from email_notifications.domain.exceptions import (
    InvalidEmailAddressError,
    EmailDeliveryError,
)
from email_notifications.domain.value_objects import EmailAddress
from email_notifications.infrastructure.smtp_adapter.smtp_sender import SMTPSender


class EmailSenderService:
    """Sends emails via SMTP adapter with configurable templates.

    Responsibilities:
    - Send individual email notifications
    - Send bulk emails with connection pooling
    - Handle SMTP errors gracefully
    - Return delivery status

    Dependencies: SMTPSender (SMTP adapter in infrastructure layer)
    """

    def __init__(self, smtp_sender: Optional[SMTPSender] = None):
        """Initialize with SMTP sender adapter.

        Args:
            smtp_sender: SMTPSender instance (default: creates new instance)
        """
        self.smtp_sender = smtp_sender or SMTPSender()

    def send_attendance_notification(
        self,
        recipient_email: str,
        context: Dict[str, Any],
    ) -> bool:
        """Send attendance notification email to student.

        Email template variables:
        - student_first_name: Student's first name
        - course_name: Course name
        - course_code: Course code
        - session_date: Session date
        - start_time: Session start time
        - end_time: Session end time
        - attendance_link: URL with embedded token
        - token_expiry: Token expiration time

        Args:
            recipient_email: Student's email address
            context: Template context dictionary

        Returns:
            True if sent successfully, False otherwise
        """
        # Validate email address
        try:
            EmailAddress(recipient_email)
        except InvalidEmailAddressError:
            return False

        if not context or not isinstance(context, dict):
            return False

        # Build email content
        subject = f"Attendance Session Created: {context.get('course_name', 'Session')}"
        body = self._build_email_body(context)

        try:
            return self.smtp_sender.send_email(
                subject=subject,
                message=body,
                from_email=self.smtp_sender.get_from_email(),
                recipient_list=[recipient_email],
                fail_silently=False,
            )
        except Exception as e:
            # Log but don't raise - return False to indicate failure
            return False

    def send_bulk_emails(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send multiple emails efficiently with connection pooling.

        Input format:
        [
            {
                "recipient_email": "john@example.com",
                "context": {...}
            },
            ...
        ]

        Args:
            emails: List of email dictionaries

        Returns:
            Summary dictionary:
            {
                "total": 200,
                "sent": 195,
                "failed": 5,
                "failed_emails": ["invalid@example.com", ...]
            }
        """
        if not emails:
            return {
                "total": 0,
                "sent": 0,
                "failed": 0,
                "failed_emails": [],
            }

        total = len(emails)
        sent_count = 0
        failed_emails = []

        try:
            # Get SMTP connection for reuse (connection pooling)
            connection = self.smtp_sender.get_connection()
            connection.open()

            try:
                for email_dict in emails:
                    recipient = email_dict.get("recipient_email")
                    context = email_dict.get("context", {})

                    if self._send_with_connection(
                        recipient, context, connection
                    ):
                        sent_count += 1
                    else:
                        failed_emails.append(recipient)

            finally:
                connection.close()

        except Exception:
            # If bulk send fails, return what we have
            pass

        return {
            "total": total,
            "sent": sent_count,
            "failed": total - sent_count,
            "failed_emails": failed_emails,
        }

    def _send_with_connection(
        self,
        recipient_email: str,
        context: Dict[str, Any],
        connection,
    ) -> bool:
        """Send single email using existing connection.

        Args:
            recipient_email: Recipient email address
            context: Template context
            connection: Django mail connection object

        Returns:
            True if sent, False otherwise
        """
        try:
            EmailAddress(recipient_email)
        except InvalidEmailAddressError:
            return False

        if not context or not isinstance(context, dict):
            return False

        try:
            subject = f"Attendance Session Created: {context.get('course_name', 'Session')}"
            body = self._build_email_body(context)

            return self.smtp_sender.send_email_with_connection(
                connection=connection,
                subject=subject,
                message=body,
                from_email=self.smtp_sender.get_from_email(),
                recipient_list=[recipient_email],
            )
        except Exception:
            return False

    def _build_email_body(self, context: Dict[str, Any]) -> str:
        """Build email body from context.

        Args:
            context: Template variables

        Returns:
            Email body text
        """
        template = """Hi {student_first_name},

Your lecturer has created an attendance session for:

Course: {course_name} ({course_code})
Date: {session_date}
Time: {start_time} - {end_time}

Click the link below to mark your attendance:
{attendance_link}

This link will expire at {token_expiry}.

Important:
- You must scan your student ID QR code
- You must be within 30 meters of the session location

Thanks,
Attendance Management System"""

        # Set defaults for missing variables
        defaults = {
            "student_first_name": "Student",
            "course_name": "Attendance Session",
            "course_code": "N/A",
            "session_date": "TBD",
            "start_time": "TBD",
            "end_time": "TBD",
            "attendance_link": "#",
            "token_expiry": "TBD",
        }
        
        # Merge provided context with defaults (context takes precedence)
        format_dict = {**defaults, **context}
        
        try:
            return template.format(**format_dict)
        except KeyError:
            # Fallback - shouldn't happen with defaults in place
            return template.format(**defaults)

    def _get_from_email(self) -> str:
        """Get sender email address from settings.

        Returns:
            From email address
        """
        return self.smtp_sender.get_from_email()
