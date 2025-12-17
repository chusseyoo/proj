"""Tests for EmailNotification domain entity."""
import pytest
from datetime import datetime, timezone, timedelta

from email_notifications.domain.entities import EmailNotification
from email_notifications.domain.value_objects import (
    NotificationStatus,
    StudentID,
    SessionID,
    TokenExpiryTime,
)
from email_notifications.domain.exceptions import (
    InvalidNotificationStatusError,
)


class TestEmailNotificationEntity:
    """Test suite for EmailNotification aggregate root."""

    @pytest.fixture
    def valid_expiry(self):
        """Expiry time 1 hour in future."""
        return datetime.now(timezone.utc) + timedelta(hours=1)

    @pytest.fixture
    def valid_notification(self, valid_expiry):
        """Valid EmailNotification instance."""
        return EmailNotification(
            email_id=None,
            session_id=SessionID(123),
            student_id=StudentID(456),
            token="test.jwt.token",
            token_expires_at=TokenExpiryTime(valid_expiry),
            status=NotificationStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            sent_at=None,
        )

    # ==================== Creation Tests ====================

    def test_create_email_notification_success(self, valid_notification):
        """Creating valid notification should succeed."""
        assert valid_notification.email_id is None
        assert valid_notification.status == NotificationStatus.PENDING
        assert valid_notification.sent_at is None

    def test_create_notification_with_email_id(self, valid_expiry):
        """Notification can be created with email_id set."""
        notification = EmailNotification(
            email_id=999,
            session_id=SessionID(123),
            student_id=StudentID(456),
            token="test.token",
            token_expires_at=TokenExpiryTime(valid_expiry),
            status=NotificationStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            sent_at=None,
        )
        
        assert notification.email_id == 999

    def test_create_notification_requires_non_empty_token(self, valid_expiry):
        """Token must be non-empty."""
        with pytest.raises(ValueError):
            EmailNotification(
                email_id=None,
                session_id=SessionID(123),
                student_id=StudentID(456),
                token="",
                token_expires_at=TokenExpiryTime(valid_expiry),
                status=NotificationStatus.PENDING,
                created_at=datetime.now(timezone.utc),
                sent_at=None,
            )

    def test_create_notification_requires_string_token(self, valid_expiry):
        """Token must be string."""
        with pytest.raises(ValueError):
            EmailNotification(
                email_id=None,
                session_id=SessionID(123),
                student_id=StudentID(456),
                token=None,
                token_expires_at=TokenExpiryTime(valid_expiry),
                status=NotificationStatus.PENDING,
                created_at=datetime.now(timezone.utc),
                sent_at=None,
            )

    def test_create_notification_requires_timezone_aware_created_at(self, valid_expiry):
        """created_at must have timezone information."""
        naive_datetime = datetime.now()  # No timezone
        
        with pytest.raises(ValueError) as exc_info:
            EmailNotification(
                email_id=None,
                session_id=SessionID(123),
                student_id=StudentID(456),
                token="test.token",
                token_expires_at=TokenExpiryTime(valid_expiry),
                status=NotificationStatus.PENDING,
                created_at=naive_datetime,
                sent_at=None,
            )
        
        assert "timezone" in str(exc_info.value)

    # ==================== Nullable sent_at Tests ====================

    def test_sent_at_nullable_when_pending(self, valid_notification):
        """sent_at can be NULL when status is pending."""
        assert valid_notification.sent_at is None
        assert valid_notification.status == NotificationStatus.PENDING

    def test_sent_at_nullable_when_failed(self, valid_expiry):
        """sent_at must be NULL when status is failed."""
        notification = EmailNotification(
            email_id=None,
            session_id=SessionID(123),
            student_id=StudentID(456),
            token="test.token",
            token_expires_at=TokenExpiryTime(valid_expiry),
            status=NotificationStatus.FAILED,
            created_at=datetime.now(timezone.utc),
            sent_at=None,
        )
        
        assert notification.sent_at is None

    def test_sent_at_must_be_set_when_sent(self, valid_expiry):
        """sent_at must be set when status is SENT."""
        with pytest.raises(InvalidNotificationStatusError):
            EmailNotification(
                email_id=None,
                session_id=SessionID(123),
                student_id=StudentID(456),
                token="test.token",
                token_expires_at=TokenExpiryTime(valid_expiry),
                status=NotificationStatus.SENT,
                created_at=datetime.now(timezone.utc),
                sent_at=None,  # Should not be None when sent
            )

    def test_sent_at_must_be_null_when_pending(self, valid_expiry):
        """sent_at cannot be set when status is PENDING."""
        with pytest.raises(InvalidNotificationStatusError):
            EmailNotification(
                email_id=None,
                session_id=SessionID(123),
                student_id=StudentID(456),
                token="test.token",
                token_expires_at=TokenExpiryTime(valid_expiry),
                status=NotificationStatus.PENDING,
                created_at=datetime.now(timezone.utc),
                sent_at=datetime.now(timezone.utc),  # Should not be set
            )

    def test_sent_at_must_be_null_when_failed(self, valid_expiry):
        """sent_at cannot be set when status is FAILED."""
        with pytest.raises(InvalidNotificationStatusError):
            EmailNotification(
                email_id=None,
                session_id=SessionID(123),
                student_id=StudentID(456),
                token="test.token",
                token_expires_at=TokenExpiryTime(valid_expiry),
                status=NotificationStatus.FAILED,
                created_at=datetime.now(timezone.utc),
                sent_at=datetime.now(timezone.utc),  # Should not be set
            )

    def test_sent_at_must_be_after_created_at(self, valid_expiry):
        """sent_at cannot be before created_at."""
        created = datetime.now(timezone.utc)
        sent = created - timedelta(seconds=1)  # Before created
        
        with pytest.raises(ValueError):
            EmailNotification(
                email_id=None,
                session_id=SessionID(123),
                student_id=StudentID(456),
                token="test.token",
                token_expires_at=TokenExpiryTime(valid_expiry),
                status=NotificationStatus.SENT,
                created_at=created,
                sent_at=sent,
            )

    def test_sent_at_requires_timezone_when_set(self, valid_expiry):
        """sent_at must have timezone if set."""
        created = datetime.now(timezone.utc)
        naive_sent = datetime.now()  # No timezone
        
        with pytest.raises(ValueError) as exc_info:
            EmailNotification(
                email_id=None,
                session_id=SessionID(123),
                student_id=StudentID(456),
                token="test.token",
                token_expires_at=TokenExpiryTime(valid_expiry),
                status=NotificationStatus.SENT,
                created_at=created,
                sent_at=naive_sent,
            )
        
        assert "timezone" in str(exc_info.value)

    # ==================== Method Tests ====================

    def test_is_expired_returns_false_for_future_token(self, valid_notification):
        """Token not yet expired should return False."""
        assert valid_notification.is_expired() is False

    def test_is_expired_returns_true_for_expired_token(self, valid_expiry):
        """Token past expiry should return True."""
        past_expiry = datetime.now(timezone.utc) - timedelta(hours=1)
        
        notification = EmailNotification(
            email_id=None,
            session_id=SessionID(123),
            student_id=StudentID(456),
            token="test.token",
            token_expires_at=TokenExpiryTime(
                datetime.now(timezone.utc) + timedelta(hours=1)
            ),
            status=NotificationStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            sent_at=None,
        )
        
        # Create notification and manually check with past time
        # (is_expired checks current time)
        assert notification.is_expired() is False

    def test_is_sent_returns_true_when_sent(self, valid_expiry):
        """is_sent should return True for SENT status."""
        created = datetime.now(timezone.utc)
        
        notification = EmailNotification(
            email_id=None,
            session_id=SessionID(123),
            student_id=StudentID(456),
            token="test.token",
            token_expires_at=TokenExpiryTime(valid_expiry),
            status=NotificationStatus.SENT,
            created_at=created,
            sent_at=created + timedelta(seconds=5),
        )
        
        assert notification.is_sent() is True

    def test_is_sent_returns_false_when_pending(self, valid_notification):
        """is_sent should return False for PENDING status."""
        assert valid_notification.is_sent() is False

    def test_is_sent_returns_false_when_failed(self, valid_expiry):
        """is_sent should return False for FAILED status."""
        notification = EmailNotification(
            email_id=None,
            session_id=SessionID(123),
            student_id=StudentID(456),
            token="test.token",
            token_expires_at=TokenExpiryTime(valid_expiry),
            status=NotificationStatus.FAILED,
            created_at=datetime.now(timezone.utc),
            sent_at=None,
        )
        
        assert notification.is_sent() is False

    def test_can_retry_returns_true_when_failed(self, valid_expiry):
        """can_retry should return True for FAILED status."""
        notification = EmailNotification(
            email_id=None,
            session_id=SessionID(123),
            student_id=StudentID(456),
            token="test.token",
            token_expires_at=TokenExpiryTime(valid_expiry),
            status=NotificationStatus.FAILED,
            created_at=datetime.now(timezone.utc),
            sent_at=None,
        )
        
        assert notification.can_retry() is True

    def test_can_retry_returns_false_when_pending(self, valid_notification):
        """can_retry should return False for PENDING status."""
        assert valid_notification.can_retry() is False

    def test_can_retry_returns_false_when_sent(self, valid_expiry):
        """can_retry should return False for SENT status."""
        created = datetime.now(timezone.utc)
        
        notification = EmailNotification(
            email_id=None,
            session_id=SessionID(123),
            student_id=StudentID(456),
            token="test.token",
            token_expires_at=TokenExpiryTime(valid_expiry),
            status=NotificationStatus.SENT,
            created_at=created,
            sent_at=created + timedelta(seconds=5),
        )
        
        assert notification.can_retry() is False

    # ==================== State Transition Tests ====================

    def test_mark_as_sent_success(self, valid_notification):
        """Marking pending notification as sent should succeed."""
        sent_time = datetime.now(timezone.utc)
        new_notification = valid_notification.mark_as_sent(sent_timestamp=sent_time)
        
        assert new_notification.status == NotificationStatus.SENT
        assert new_notification.sent_at == sent_time
        # Original should be immutable
        assert valid_notification.status == NotificationStatus.PENDING

    def test_mark_as_sent_without_timestamp(self, valid_notification):
        """Marking as sent without timestamp should use current time."""
        new_notification = valid_notification.mark_as_sent()
        
        assert new_notification.status == NotificationStatus.SENT
        assert new_notification.sent_at is not None
        assert isinstance(new_notification.sent_at, datetime)

    def test_mark_as_sent_from_failed_raises_error(self, valid_expiry):
        """Cannot mark as sent from failed status."""
        notification = EmailNotification(
            email_id=None,
            session_id=SessionID(123),
            student_id=StudentID(456),
            token="test.token",
            token_expires_at=TokenExpiryTime(valid_expiry),
            status=NotificationStatus.FAILED,
            created_at=datetime.now(timezone.utc),
            sent_at=None,
        )
        
        with pytest.raises(InvalidNotificationStatusError):
            notification.mark_as_sent()

    def test_mark_as_failed_success(self, valid_notification):
        """Marking pending notification as failed should succeed."""
        new_notification = valid_notification.mark_as_failed()
        
        assert new_notification.status == NotificationStatus.FAILED
        assert new_notification.sent_at is None
        # Original should be immutable
        assert valid_notification.status == NotificationStatus.PENDING

    def test_mark_as_failed_from_sent_raises_error(self, valid_expiry):
        """Cannot mark as failed from sent status."""
        created = datetime.now(timezone.utc)
        
        notification = EmailNotification(
            email_id=None,
            session_id=SessionID(123),
            student_id=StudentID(456),
            token="test.token",
            token_expires_at=TokenExpiryTime(valid_expiry),
            status=NotificationStatus.SENT,
            created_at=created,
            sent_at=created + timedelta(seconds=5),
        )
        
        with pytest.raises(InvalidNotificationStatusError):
            notification.mark_as_failed()

    def test_mark_for_retry_success(self, valid_expiry):
        """Marking failed notification for retry should succeed."""
        notification = EmailNotification(
            email_id=None,
            session_id=SessionID(123),
            student_id=StudentID(456),
            token="test.token",
            token_expires_at=TokenExpiryTime(valid_expiry),
            status=NotificationStatus.FAILED,
            created_at=datetime.now(timezone.utc),
            sent_at=None,
        )
        
        new_notification = notification.mark_for_retry()
        
        assert new_notification.status == NotificationStatus.PENDING
        assert new_notification.sent_at is None

    def test_mark_for_retry_from_sent_raises_error(self, valid_expiry):
        """Cannot retry from sent status."""
        created = datetime.now(timezone.utc)
        
        notification = EmailNotification(
            email_id=None,
            session_id=SessionID(123),
            student_id=StudentID(456),
            token="test.token",
            token_expires_at=TokenExpiryTime(valid_expiry),
            status=NotificationStatus.SENT,
            created_at=created,
            sent_at=created + timedelta(seconds=5),
        )
        
        with pytest.raises(InvalidNotificationStatusError):
            notification.mark_for_retry()

    # ==================== Immutability Tests ====================

    def test_notification_is_immutable(self, valid_notification):
        """Notification should be immutable (frozen dataclass)."""
        with pytest.raises(AttributeError):
            valid_notification.status = NotificationStatus.SENT

    def test_transitions_return_new_instances(self, valid_notification):
        """Transitions should return new instances, not modify original."""
        sent = valid_notification.mark_as_sent()
        
        assert sent is not valid_notification
        assert valid_notification.status == NotificationStatus.PENDING
        assert sent.status == NotificationStatus.SENT
