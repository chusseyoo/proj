"""EmailNotification repository for data access."""
from typing import List, Dict, Any, Optional
from datetime import timedelta

from django.db.models import QuerySet
from django.utils import timezone

from email_notifications.models import EmailNotification


class EmailNotificationRepository:
    """Repository for EmailNotification entity persistence.
    
    Responsibilities:
    - CRUD operations for EmailNotification
    - Status-based queries (pending, sent, failed)
    - Bulk creation for efficiency
    - Token lookup for attendance validation
    - Session/student filtering
    """

    # ==================== CRUD Operations ====================

    @staticmethod
    def create(data: Dict[str, Any]) -> EmailNotification:
        """Create single notification.
        
        Args:
            data: Dictionary with keys:
                - session_id: int
                - student_profile_id: int
                - token: str
                - token_expires_at: datetime
                - status: str (optional, default 'pending')
        
        Returns:
            Saved EmailNotification instance
            
        Raises:
            IntegrityError: If duplicate (session + student)
            ForeignKey.DoesNotExist: If invalid FK reference
        """
        notification = EmailNotification.objects.create(**data)
        return notification

    @staticmethod
    def bulk_create(notifications: List[Dict[str, Any]]) -> List[EmailNotification]:
        """Create multiple notifications efficiently.
        
        Args:
            notifications: List of notification dictionaries
            
        Returns:
            List of created EmailNotification instances
            
        Note:
            Single database transaction vs N individual inserts
            Critical for sessions with many students
        """
        notification_objs = [
            EmailNotification(**data) for data in notifications
        ]
        return EmailNotification.objects.bulk_create(notification_objs)

    @staticmethod
    def get_by_id(email_id: int) -> EmailNotification:
        """Retrieve notification by primary key.
        
        Args:
            email_id: Primary key
            
        Returns:
            EmailNotification instance
            
        Raises:
            EmailNotification.DoesNotExist: If not found
        """
        return EmailNotification.objects.get(email_id=email_id)

    @staticmethod
    def get_by_token(token: str) -> Optional[EmailNotification]:
        """Find notification by JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            EmailNotification or None if not found
            
        Note:
            Critical for attendance marking - token identifies student/session
            Indexed for performance
        """
        return EmailNotification.objects.filter(token=token).first()

    @staticmethod
    def update_status(
        email_id: int,
        new_status: str,
        sent_at: Optional[timezone.datetime] = None
    ) -> EmailNotification:
        """Update notification status.
        
        Args:
            email_id: Primary key
            new_status: New status value
            sent_at: Optional timestamp (only for 'sent' status)
            
        Returns:
            Updated EmailNotification instance
            
        Raises:
            EmailNotification.DoesNotExist: If not found
            ValueError: If transition is not allowed
        """
        notification = EmailNotification.objects.get(email_id=email_id)
        current = notification.status

        # Disallow modifying already sent notifications
        if current == EmailNotification.Status.SENT and new_status != EmailNotification.Status.SENT:
            raise ValueError("Cannot change status of a sent notification")

        if current == EmailNotification.Status.PENDING:
            if new_status == EmailNotification.Status.SENT:
                notification.sent_at = sent_at or timezone.now()
            elif new_status == EmailNotification.Status.FAILED:
                notification.sent_at = None
            elif new_status == EmailNotification.Status.PENDING:
                pass
            else:
                raise ValueError(f"Unsupported status transition: {current} -> {new_status}")
        elif current == EmailNotification.Status.FAILED:
            if new_status == EmailNotification.Status.PENDING:
                notification.sent_at = None
            elif new_status == EmailNotification.Status.SENT:
                notification.sent_at = sent_at or timezone.now()
            elif new_status == EmailNotification.Status.FAILED:
                pass
            else:
                raise ValueError(f"Unsupported status transition: {current} -> {new_status}")

        notification.status = new_status
        notification.save()
        return notification

    @staticmethod
    def delete(email_id: int) -> None:
        """Delete notification.
        
        Args:
            email_id: Primary key
        """
        EmailNotification.objects.filter(email_id=email_id).delete()

    # ==================== Status Queries ====================

    @staticmethod
    def get_pending_emails(limit: int = 100) -> QuerySet:
        """Get pending emails for background worker.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            QuerySet ordered by created_at (FIFO)
        """
        return EmailNotification.objects.filter(
            status=EmailNotification.Status.PENDING
        ).order_by("created_at")[:limit]

    @staticmethod
    def get_failed_emails(limit: int = 100) -> QuerySet:
        """Get failed emails for admin retry.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            QuerySet of failed notifications
        """
        return EmailNotification.objects.filter(
            status=EmailNotification.Status.FAILED
        ).order_by("-created_at")[:limit]

    @staticmethod
    def count_by_status() -> Dict[str, int]:
        """Get count statistics by status.
        
        Returns:
            Dictionary with counts per status
        """
        counts = {}
        for status, _ in EmailNotification.Status.choices:
            counts[status] = EmailNotification.objects.filter(
                status=status
            ).count()
        return counts

    # ==================== Context Queries ====================

    @staticmethod
    def get_by_session(session_id: int) -> QuerySet:
        """Get all notifications for a session.
        
        Args:
            session_id: Session primary key
            
        Returns:
            QuerySet of notifications for this session
        """
        return EmailNotification.objects.filter(
            session_id=session_id
        ).select_related(
            "session",
            "student_profile__user",
        ).order_by("created_at")

    @staticmethod
    def get_by_student(student_profile_id: int) -> QuerySet:
        """Get student's notification history.
        
        Args:
            student_profile_id: Student profile primary key
            
        Returns:
            QuerySet ordered by created_at (newest first)
        """
        return EmailNotification.objects.filter(
            student_profile_id=student_profile_id
        ).select_related(
            "session",
            "student_profile__user",
        ).order_by("-created_at")

    @staticmethod
    def exists_for_session_and_student(
        session_id: int,
        student_profile_id: int
    ) -> bool:
        """Check if notification already exists (duplicate prevention).
        
        Args:
            session_id: Session primary key
            student_profile_id: Student primary key
            
        Returns:
            True if exists, False otherwise
        """
        return EmailNotification.objects.filter(
            session_id=session_id,
            student_profile_id=student_profile_id
        ).exists()

    # ==================== Maintenance Queries ====================

    @staticmethod
    def get_expired_tokens() -> QuerySet:
        """Get notifications with expired tokens (cleanup query).
        
        Returns:
            QuerySet of notifications with expired tokens
        """
        return EmailNotification.objects.filter(
            token_expires_at__lt=timezone.now()
        ).order_by("token_expires_at")

    @staticmethod
    def delete_expired(older_than_days: int = 30) -> int:
        """Bulk delete old expired notifications.
        
        Args:
            older_than_days: Delete records whose token_expires_at is older than this many days
            
        Returns:
            Number of records deleted
        """
        cutoff = timezone.now() - timedelta(days=older_than_days)
        count, _ = EmailNotification.objects.filter(
            token_expires_at__lt=cutoff
        ).delete()
        return count

    # ==================== Reporting Queries ====================

    @staticmethod
    def get_delivery_statistics(session_id: Optional[int] = None) -> Dict[str, Any]:
        """Get metrics and success rates.
        
        Args:
            session_id: Optional session filter (None for all)
        
        Returns:
            Dictionary with:
                - total: Total notifications
                - sent: Successfully sent count
                - failed: Failed count
                - pending: Still pending count
                - success_rate: Percentage sent over sent+failed
        """
        qs = EmailNotification.objects.all()
        if session_id is not None:
            qs = qs.filter(session_id=session_id)

        sent = qs.filter(status=EmailNotification.Status.SENT).count()
        failed = qs.filter(status=EmailNotification.Status.FAILED).count()
        pending = qs.filter(status=EmailNotification.Status.PENDING).count()
        total = sent + failed + pending

        denom = sent + failed
        success_rate = (sent / denom * 100) if denom > 0 else 0

        return {
            "total": total,
            "sent": sent,
            "failed": failed,
            "pending": pending,
            "success_rate": round(success_rate, 2),
        }
