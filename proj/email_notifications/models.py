"""EmailNotification ORM model for Django."""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class EmailNotification(models.Model):
    """Notification entity representing an email sent to a student for a session.
    
    Aggregate Root responsibilities:
    - Store notification state (pending, sent, failed)
    - Track creation and delivery timestamps
    - Maintain JWT token for attendance link
    
    Database constraints:
    - One email per (session, student) pair
    - Token expiry must be in future
    - sent_at can only be set when status='sent'
    """

    class Status(models.TextChoices):
        """Email delivery status choices."""
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    # Primary key
    email_id = models.AutoField(primary_key=True)

    # Foreign keys
    session = models.ForeignKey(
        "session_management.Session",
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="Session this notification is for"
    )
    student_profile = models.ForeignKey(
        "user_management.StudentProfile",
        on_delete=models.CASCADE,
        related_name="email_notifications",
        help_text="Student recipient of this notification"
    )

    # Token
    token = models.TextField(
        help_text="JWT token for attendance link"
    )
    token_expires_at = models.DateTimeField(
        help_text="When the JWT token expires"
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        help_text="Email delivery status"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When notification was created"
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When email was successfully sent (NULL if not sent)"
    )

    class Meta:
        db_table = "email_notifications"
        indexes = [
            models.Index(fields=["session"], name="idx_email_session_id"),
            models.Index(fields=["student_profile"], name="idx_email_student_id"),
            models.Index(fields=["status"], name="idx_email_status"),
            models.Index(fields=["token"], name="idx_email_token"),
            models.Index(fields=["created_at"], name="idx_email_created_at"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "student_profile"],
                name="unique_email_per_student_session",
                violation_error_message="Email already exists for this student in this session"
            ),
            models.CheckConstraint(
                condition=models.Q(token_expires_at__gt=models.F("created_at")),
                name="token_expiry_future",
                violation_error_message="Token expiry must be after creation time"
            ),
        ]
        verbose_name = "Email Notification"
        verbose_name_plural = "Email Notifications"
        ordering = ["created_at"]

    def __str__(self) -> str:
        """String representation."""
        return f"Email#{self.email_id} - {self.get_status_display()} - Session#{self.session_id}"

    def save(self, *args, **kwargs):
        """Validate before saving."""
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        """Validate model constraints."""
        # Check token expiry is in future
        if self.token_expires_at and self.created_at:
            if self.token_expires_at <= self.created_at:
                raise ValidationError(
                    {"token_expires_at": "Token expiry must be after creation time"}
                )

        # sent_at validation
        if self.sent_at is not None:
            if self.status != self.Status.SENT:
                raise ValidationError(
                    {"sent_at": "sent_at can only be set when status='sent'"}
                )
            if self.sent_at < self.created_at:
                raise ValidationError(
                    {"sent_at": "sent_at must be after created_at"}
                )

    @property
    def is_pending(self) -> bool:
        """Check if notification is pending."""
        return self.status == self.Status.PENDING

    @property
    def is_sent(self) -> bool:
        """Check if notification was sent."""
        return self.status == self.Status.SENT

    @property
    def is_failed(self) -> bool:
        """Check if sending failed."""
        return self.status == self.Status.FAILED

    @property
    def is_token_expired(self) -> bool:
        """Check if JWT token is expired."""
        return timezone.now() > self.token_expires_at

    def mark_as_sent(self, sent_at: timezone.datetime = None) -> None:
        """Mark notification as sent.
        
        Args:
            sent_at: Timestamp when sent (defaults to now)
            
        Raises:
            ValueError: If status is not pending or already sent
        """
        if self.status != self.Status.PENDING:
            raise ValueError(
                f"Cannot mark as sent - current status is {self.status}"
            )
        
        self.status = self.Status.SENT
        self.sent_at = sent_at or timezone.now()
        self.save()

    def mark_as_failed(self) -> None:
        """Mark notification as failed.
        
        Raises:
            ValueError: If status is sent
        """
        if self.status == self.Status.SENT:
            raise ValueError("Cannot mark sent notification as failed")
        
        self.status = self.Status.FAILED
        self.save()

    def mark_for_retry(self) -> None:
        """Mark failed notification for retry.
        
        Raises:
            ValueError: If status is not failed
        """
        if self.status != self.Status.FAILED:
            raise ValueError(
                f"Can only retry failed notifications, current status is {self.status}"
            )
        
        self.status = self.Status.PENDING
        self.sent_at = None
        self.save()
