"""Publisher utilities for safe event publishing.

Provides helpers to ensure events are published only after successful
database commits.
"""

from typing import Dict, Any

from django.db import transaction

from ...application.ports.ports import EventPublisherPort


def publish_after_commit(
    publisher: EventPublisherPort,
    event_name: str,
    payload: Dict[str, Any]
) -> None:
    """Publish an event only after the current database transaction commits.
    
    This ensures that events are only published if the database operation
    succeeds. If the transaction rolls back, the event will not be published.
    
    Args:
        publisher: The event publisher instance to use
        event_name: Name of the event to publish
        payload: Event payload data
        
    Example:
        # In a use-case or service
        saved = session_repository.save(domain_session)
        publish_after_commit(
            publisher,
            "session.created",
            {"session_id": saved.session_id, "lecturer_id": saved.lecturer_id}
        )
        
    Note:
        If called outside a transaction, the event is published immediately.
    """
    transaction.on_commit(lambda: publisher.publish(event_name, payload))
