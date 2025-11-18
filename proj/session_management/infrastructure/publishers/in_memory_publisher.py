from __future__ import annotations

from typing import Dict, Any, List

from ...application.ports.ports import EventPublisherPort


class InMemoryPublisher(EventPublisherPort):
    """A simple in-memory event publisher for tests and local runs.

    It records published events in `events` list as tuples: (event_name, payload).
    """

    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []

    def publish(self, event_name: str, payload: Dict[str, Any]) -> None:
        self.events.append({"event": event_name, "payload": payload})
