"""SMTP adapter for sending emails via Django mail backend."""
from typing import List, Optional
from django.core.mail import send_mail, get_connection, EmailMessage
from django.conf import settings


class SMTPSender:
    """Adapter for sending emails via SMTP backend.
    
    Wraps Django's email backend to:
    - Provide consistent interface for email sending
    - Handle connection pooling
    - Centralize SMTP configuration
    - Separate infrastructure from business logic
    """

    def __init__(self, email_backend=None):
        """Initialize SMTP adapter.
        
        Args:
            email_backend: Django email backend instance (default: configured backend)
        """
        self.email_backend = email_backend

    def send_email(
        self,
        subject: str,
        message: str,
        from_email: str,
        recipient_list: List[str],
        fail_silently: bool = False,
    ) -> bool:
        """Send single email via SMTP.
        
        Args:
            subject: Email subject
            message: Email body
            from_email: Sender email address
            recipient_list: List of recipient emails
            fail_silently: Whether to suppress exceptions
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            num_sent = send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=fail_silently,
            )
            return num_sent > 0
        except Exception as e:
            if not fail_silently:
                raise
            return False

    def send_email_with_connection(
        self,
        connection,
        subject: str,
        message: str,
        from_email: str,
        recipient_list: List[str],
    ) -> bool:
        """Send single email using existing SMTP connection.
        
        Args:
            connection: Django mail connection object
            subject: Email subject
            message: Email body
            from_email: Sender email address
            recipient_list: List of recipient emails
            
        Returns:
            True if sent, False otherwise
        """
        try:
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=from_email,
                to=recipient_list,
                connection=connection,
            )
            num_sent = email.send(fail_silently=False)
            return num_sent > 0
        except Exception:
            return False

    def get_connection(self):
        """Get SMTP connection for connection pooling.
        
        Returns:
            Django mail connection object
        """
        return get_connection(backend=self.email_backend)

    def get_from_email(self) -> str:
        """Get configured from email address.
        
        Returns:
            From email address
        """
        try:
            return getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost")
        except Exception:
            return "noreply@localhost"
