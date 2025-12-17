"""Tests for NotificationGenerationService domain service."""
import pytest
from datetime import datetime, timezone, timedelta

from email_notifications.domain.services import (
    NotificationGenerationService,
    JWTTokenService,
)
from email_notifications.domain.entities import EmailNotification
from email_notifications.domain.value_objects import NotificationStatus
from email_notifications.domain.exceptions import (
    InvalidTokenExpiryError,
)


class TestNotificationGenerationService:
    """Test suite for notification generation service."""

    @pytest.fixture
    def jwt_service(self):
        """Create JWT service."""
        return JWTTokenService(secret_key="test-secret")

    @pytest.fixture
    def gen_service(self, jwt_service):
        """Create notification generation service."""
        return NotificationGenerationService(
            jwt_service=jwt_service,
            token_expiry_minutes=60,
        )

    @pytest.fixture
    def session_start_time(self):
        """Session start time 1 hour from now."""
        return datetime.now(timezone.utc) + timedelta(hours=1)

    @pytest.fixture
    def eligible_students(self):
        """Sample list of eligible students."""
        return [
            {"student_profile_id": 1, "name": "Alice"},
            {"student_profile_id": 2, "name": "Bob"},
            {"student_profile_id": 3, "name": "Charlie"},
        ]

    # ==================== Basic Generation Tests ====================

    def test_generate_notifications_for_session_success(
        self, gen_service, session_start_time, eligible_students
    ):
        """Generating notifications should create notification for each student."""
        result = gen_service.generate_notifications_for_session(
            session_id=123,
            session_start_time=session_start_time,
            eligible_students=eligible_students,
        )
        
        assert result["session_id"] == 123
        assert result["count"] == 3
        assert len(result["notifications"]) == 3

    def test_generate_notifications_returns_email_notification_entities(
        self, gen_service, session_start_time, eligible_students
    ):
        """Generated notifications should be EmailNotification entities."""
        result = gen_service.generate_notifications_for_session(
            session_id=123,
            session_start_time=session_start_time,
            eligible_students=eligible_students,
        )
        
        for notification in result["notifications"]:
            assert isinstance(notification, EmailNotification)

    def test_generate_notifications_all_pending_status(
        self, gen_service, session_start_time, eligible_students
    ):
        """All generated notifications should have pending status."""
        result = gen_service.generate_notifications_for_session(
            session_id=123,
            session_start_time=session_start_time,
            eligible_students=eligible_students,
        )
        
        for notification in result["notifications"]:
            assert notification.status == NotificationStatus.PENDING

    def test_generate_notifications_no_sent_at(
        self, gen_service, session_start_time, eligible_students
    ):
        """Generated notifications should not have sent_at set."""
        result = gen_service.generate_notifications_for_session(
            session_id=123,
            session_start_time=session_start_time,
            eligible_students=eligible_students,
        )
        
        for notification in result["notifications"]:
            assert notification.sent_at is None

    def test_generate_notifications_empty_students_list(
        self, gen_service, session_start_time
    ):
        """Empty student list should return 0 notifications."""
        result = gen_service.generate_notifications_for_session(
            session_id=123,
            session_start_time=session_start_time,
            eligible_students=[],
        )
        
        assert result["count"] == 0
        assert result["notifications"] == []

    # ==================== Token Generation Tests ====================

    def test_generate_notifications_each_student_gets_unique_token(
        self, gen_service, session_start_time, eligible_students
    ):
        """Each student should get a unique JWT token."""
        result = gen_service.generate_notifications_for_session(
            session_id=123,
            session_start_time=session_start_time,
            eligible_students=eligible_students,
        )
        
        tokens = [n.token for n in result["notifications"]]
        
        # All tokens should be unique
        assert len(tokens) == len(set(tokens))

    def test_generate_notifications_token_contains_student_id(
        self, gen_service, session_start_time, eligible_students, jwt_service
    ):
        """Token payload should contain correct student_profile_id."""
        result = gen_service.generate_notifications_for_session(
            session_id=123,
            session_start_time=session_start_time,
            eligible_students=eligible_students,
        )
        
        for notification in result["notifications"]:
            payload = jwt_service.decode_token(notification.token)
            assert payload["student_profile_id"] == int(notification.student_id.value)

    def test_generate_notifications_token_contains_session_id(
        self, gen_service, session_start_time, eligible_students, jwt_service
    ):
        """Token payload should contain correct session_id."""
        result = gen_service.generate_notifications_for_session(
            session_id=456,
            session_start_time=session_start_time,
            eligible_students=eligible_students,
        )
        
        for notification in result["notifications"]:
            payload = jwt_service.decode_token(notification.token)
            assert payload["session_id"] == 456

    # ==================== Expiry Time Tests ====================

    def test_generate_notifications_expiry_is_session_start_plus_minutes(
        self, session_start_time, eligible_students
    ):
        """Token expiry should be session_start + token_expiry_minutes."""
        gen_service = NotificationGenerationService(
            jwt_service=JWTTokenService(secret_key="test"),
            token_expiry_minutes=60,
        )
        
        result = gen_service.generate_notifications_for_session(
            session_id=123,
            session_start_time=session_start_time,
            eligible_students=eligible_students,
        )
        
        expected_expiry = session_start_time + timedelta(minutes=60)
        
        for notification in result["notifications"]:
            # Check expiry is within 1 second of expected
            exp_timestamp = int(notification.token_expires_at.expires_at.timestamp())
            expected_timestamp = int(expected_expiry.timestamp())
            assert abs(exp_timestamp - expected_timestamp) <= 1

    def test_generate_notifications_custom_expiry_minutes(
        self, session_start_time, eligible_students
    ):
        """Custom token_expiry_minutes should be respected."""
        gen_service = NotificationGenerationService(
            jwt_service=JWTTokenService(secret_key="test"),
            token_expiry_minutes=30,
        )
        
        result = gen_service.generate_notifications_for_session(
            session_id=123,
            session_start_time=session_start_time,
            eligible_students=eligible_students,
        )
        
        expected_expiry = session_start_time + timedelta(minutes=30)
        
        for notification in result["notifications"]:
            exp_timestamp = int(notification.token_expires_at.expires_at.timestamp())
            expected_timestamp = int(expected_expiry.timestamp())
            assert abs(exp_timestamp - expected_timestamp) <= 1

    def test_generate_notifications_with_past_session_time_raises_error(
        self, gen_service, eligible_students
    ):
        """Session start time in past would create past expiry, should raise error."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)
        
        with pytest.raises(InvalidTokenExpiryError):
            gen_service.generate_notifications_for_session(
                session_id=123,
                session_start_time=past_time,
                eligible_students=eligible_students,
            )

    # ==================== Session and Student ID Tests ====================

    def test_generate_notifications_correct_session_id(
        self, gen_service, session_start_time, eligible_students
    ):
        """All notifications should reference correct session."""
        result = gen_service.generate_notifications_for_session(
            session_id=999,
            session_start_time=session_start_time,
            eligible_students=eligible_students,
        )
        
        for notification in result["notifications"]:
            assert int(notification.session_id.value) == 999

    def test_generate_notifications_correct_student_ids(
        self, gen_service, session_start_time, eligible_students
    ):
        """Each notification should reference correct student."""
        result = gen_service.generate_notifications_for_session(
            session_id=123,
            session_start_time=session_start_time,
            eligible_students=eligible_students,
        )
        
        student_ids = [n.student_id.value for n in result["notifications"]]
        expected_ids = [s["student_profile_id"] for s in eligible_students]
        
        assert set(student_ids) == set(expected_ids)

    # ==================== Edge Cases ====================

    def test_generate_notifications_students_with_missing_profile_id(
        self, gen_service, session_start_time
    ):
        """Students without student_profile_id should be skipped."""
        students = [
            {"student_profile_id": 1},
            {"name": "NoID"},  # Missing ID
            {"student_profile_id": 2},
        ]
        
        result = gen_service.generate_notifications_for_session(
            session_id=123,
            session_start_time=session_start_time,
            eligible_students=students,
        )
        
        # Should only create 2 notifications (skipping one with no ID)
        assert result["count"] == 2

    def test_generate_notifications_none_student_profile_id(
        self, gen_service, session_start_time
    ):
        """Students with None profile ID should be skipped."""
        students = [
            {"student_profile_id": 1},
            {"student_profile_id": None},
            {"student_profile_id": 2},
        ]
        
        result = gen_service.generate_notifications_for_session(
            session_id=123,
            session_start_time=session_start_time,
            eligible_students=students,
        )
        
        assert result["count"] == 2

    def test_generate_notifications_zero_student_profile_id(
        self, gen_service, session_start_time
    ):
        """Students with ID 0 should be skipped (falsy value)."""
        students = [
            {"student_profile_id": 1},
            {"student_profile_id": 0},  # Falsy
            {"student_profile_id": 2},
        ]
        
        result = gen_service.generate_notifications_for_session(
            session_id=123,
            session_start_time=session_start_time,
            eligible_students=students,
        )
        
        assert result["count"] == 2

    def test_generate_notifications_large_batch(self, gen_service, session_start_time):
        """Should handle large number of students efficiently."""
        # Create 200 students
        students = [
            {"student_profile_id": i} for i in range(1, 201)
        ]
        
        result = gen_service.generate_notifications_for_session(
            session_id=123,
            session_start_time=session_start_time,
            eligible_students=students,
        )
        
        assert result["count"] == 200
        assert len(result["notifications"]) == 200

    # ==================== Single Entity Creation Tests ====================

    def test_create_notification_entity_success(
        self, gen_service, session_start_time
    ):
        """Creating single notification entity should work."""
        exp_time = session_start_time + timedelta(hours=1)
        
        notification = gen_service.create_notification_entity(
            session_id=123,
            student_profile_id=456,
            token="test-token",
            token_expires_at=exp_time,
            status=NotificationStatus.PENDING,
        )
        
        assert isinstance(notification, EmailNotification)
        assert notification.session_id.value == 123
        assert notification.student_id.value == 456
        assert notification.token == "test-token"
        assert notification.status == NotificationStatus.PENDING

    def test_create_notification_entity_defaults(self, gen_service, session_start_time):
        """Default status should be PENDING."""
        exp_time = session_start_time + timedelta(hours=1)
        
        notification = gen_service.create_notification_entity(
            session_id=123,
            student_profile_id=456,
            token="test-token",
            token_expires_at=exp_time,
        )
        
        assert notification.status == NotificationStatus.PENDING

    # ==================== Integration Tests ====================

    def test_generate_and_validate_tokens(
        self, gen_service, session_start_time, eligible_students, jwt_service
    ):
        """All generated tokens should be valid and decodable."""
        result = gen_service.generate_notifications_for_session(
            session_id=123,
            session_start_time=session_start_time,
            eligible_students=eligible_students,
        )
        
        for notification in result["notifications"]:
            # Token should be valid
            assert jwt_service.validate_token(notification.token) is True
            
            # Token should be decodable
            payload = jwt_service.decode_token(notification.token)
            assert payload["student_profile_id"] == notification.student_id.value
            assert payload["session_id"] == notification.session_id.value
