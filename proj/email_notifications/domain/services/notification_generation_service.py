"""Notification generation and orchestration service."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

from email_notifications.domain.entities import EmailNotification
from email_notifications.domain.value_objects import (
    NotificationStatus,
    StudentID,
    SessionID,
    TokenExpiryTime,
)
from email_notifications.domain.services.jwt_service import JWTTokenService
from email_notifications.domain.exceptions import (
    SessionNotFoundError,
    TokenGenerationError,
    InvalidTokenExpiryError,
)


class NotificationGenerationService:
    """Orchestrates email notification creation for eligible students.

    Responsibilities:
    - Determine eligible students for a session
    - Generate unique JWT token for each student
    - Create EmailNotification entities in bulk
    - Support retry workflow for failed notifications

    Workflow:
    1. Get session details (program, stream, timing)
    2. Query eligible students (active, matching program/stream)
    3. Generate token for each student
    4. Create notification entities with status=pending
    5. Return bulk entities for repository to persist
    """

    def __init__(
        self,
        jwt_service: JWTTokenService,
        token_expiry_minutes: int = 30,
    ):
        """Initialize service dependencies.

        Args:
            jwt_service: JWT token generator
            token_expiry_minutes: Token validity duration (default 30 mins)
        """
        self.jwt_service = jwt_service
        self.token_expiry_minutes = token_expiry_minutes

    def generate_notifications_for_session(
        self,
        session_id: int,
        session_start_time: datetime,
        eligible_students: List[Dict[str, int]],
    ) -> Dict[str, Any]:
        """Create notifications for all eligible students in a session.

        Workflow:
        1. Calculate token expiry time (session start + expiry_minutes)
        2. For each eligible student:
           - Generate unique JWT token
           - Create EmailNotification entity
        3. Return created entities for repository to persist

        Args:
            session_id: Session ID
            session_start_time: When session starts (datetime with timezone)
            eligible_students: List of student dicts with 'student_profile_id'

        Returns:
            Dictionary with:
            {
                "session_id": 123,
                "notifications": [EmailNotification, ...],
                "count": 200,
            }

        Raises:
            TokenGenerationError: Failed to generate token
            InvalidTokenExpiryError: Invalid expiry time
        """
        if not eligible_students:
            return {
                "session_id": session_id,
                "notifications": [],
                "count": 0,
            }

        # Calculate token expiry: session start + token_expiry_minutes
        token_expiry = session_start_time + timedelta(
            minutes=self.token_expiry_minutes
        )

        # Validate expiry is in future
        try:
            TokenExpiryTime(token_expiry)
        except InvalidTokenExpiryError as e:
            raise InvalidTokenExpiryError(
                f"Cannot generate notifications with past expiry: {str(e)}"
            )

        # Generate notifications
        notifications = []
        for student in eligible_students:
            student_profile_id = student.get("student_profile_id")

            if not student_profile_id:
                continue

            try:
                # Generate unique token for this student-session pair
                token = self.jwt_service.generate_token(
                    student_profile_id=student_profile_id,
                    session_id=session_id,
                    expires_at=token_expiry,
                )

                # Create notification entity
                notification = EmailNotification(
                    email_id=None,
                    session_id=SessionID(session_id),
                    student_id=StudentID(student_profile_id),
                    token=token,
                    token_expires_at=TokenExpiryTime(token_expiry),
                    status=NotificationStatus.PENDING,
                    created_at=datetime.now(timezone.utc),
                    sent_at=None,
                )

                notifications.append(notification)

            except (TokenGenerationError, InvalidTokenExpiryError) as e:
                # Log individual token generation failure, but continue
                # In production, this would log to error tracking
                continue

        return {
            "session_id": session_id,
            "notifications": notifications,
            "count": len(notifications),
        }

    def create_notification_entity(
        self,
        session_id: int,
        student_profile_id: int,
        token: str,
        token_expires_at: datetime,
        status: NotificationStatus = NotificationStatus.PENDING,
    ) -> EmailNotification:
        """Create a single notification entity.

        Used when creating individual notifications (not bulk).

        Args:
            session_id: Session ID
            student_profile_id: Student profile ID
            token: JWT token
            token_expires_at: Token expiration time
            status: Initial status (default: PENDING)

        Returns:
            EmailNotification entity

        Raises:
            Various validation errors from entity
        """
        return EmailNotification(
            email_id=None,
            session_id=SessionID(session_id),
            student_id=StudentID(student_profile_id),
            token=token,
            token_expires_at=TokenExpiryTime(token_expires_at),
            status=status,
            created_at=datetime.now(timezone.utc),
            sent_at=None,
        )
