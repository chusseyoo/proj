from __future__ import annotations

from typing import Protocol, Any, Dict


class EventPublisherPort(Protocol):
    """Simple event publisher port for application-side events (SessionCreated, ...)."""

    def publish(self, event_name: str, payload: Dict[str, Any]) -> None:
        ...
