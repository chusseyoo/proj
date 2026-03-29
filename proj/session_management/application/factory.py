"""Simple DI factory helpers for wiring application use-cases.

This module provides two convenience helpers used by tests and small scripts:
- `build_app_usecases(...)` returns instantiated use-case objects wired with the
  provided repository, academic and user ports and optional publisher.
- `build_inmemory_container()` is a small convenience that builds in-memory
  adapters and returns the use-cases plus the adapters for inspection in tests.

Keep this intentionally tiny and dependency-free (no framework wiring).
"""
from __future__ import annotations

from typing import Dict

from .in_memory_adapters import (
    InMemoryAcademicPort,
    EventDispatcher,
    InMemorySessionRepository,
    InMemoryUserPort,
)

from .use_cases.create_session import CreateSessionUseCase
from .use_cases.list_sessions import ListMySessionsUseCase
from .use_cases.get_session import GetSessionUseCase
from .use_cases.end_session import EndSessionUseCase
from .use_cases.update_session import UpdateSessionUseCase

from ..domain.services.session_rules import SessionService


def build_app_usecases(repository, academic_port, user_port, publisher=None) -> Dict[str, object]:
    """Return a dict of use-case instances wired with the provided ports.

    Keys returned: create, list, get, end, update, service
    """
    service = SessionService(repository=repository, academic_port=academic_port, user_port=user_port)

    create_uc = CreateSessionUseCase(repository=repository, service=service, publisher=publisher)
    list_uc = ListMySessionsUseCase(repository=repository, service=service)
    get_uc = GetSessionUseCase(repository=repository, service=service)
    end_uc = EndSessionUseCase(repository=repository, service=service)
    update_uc = UpdateSessionUseCase(repository=repository, service=service)

    return {
        "create": create_uc,
        "list": list_uc,
        "get": get_uc,
        "end": end_uc,
        "update": update_uc,
        "service": service,
    }


def build_inmemory_container(course_lecturer_map: dict | None = None, active_lecturers: set | None = None) -> Dict[str, object]:
    """Build in-memory adapters and return a container dict with adapters and use-cases.

    Useful for tests that want to inspect published events or repository contents.
    
    Automatically wires session.created event to notification generation via EventDispatcher.
    """
    repo = InMemorySessionRepository()
    academic = InMemoryAcademicPort(course_lecturer_map=course_lecturer_map)
    users = InMemoryUserPort(active_lecturers=active_lecturers)

    # Wire event handler for session.created -> notification generation
    def handle_session_created(payload: dict):
        """When a session is created, enqueue async notification generation."""
        try:
            from email_notifications.tasks import generate_notifications_for_session_task
            
            session_id = payload.get("session_id")
            if not session_id:
                return  # Silently skip if no session_id in event

            generate_notifications_for_session_task.delay(session_id=session_id)
        except Exception as e:
            # Non-blocking: log and continue
            # In production, this would be logged and monitored
            import sys
            print(f"[handle_session_created] Failed to generate notifications for session {payload.get('session_id')}: {e}", file=sys.stderr)
    
    publisher = EventDispatcher(handlers={"session.created": handle_session_created})
    usecases = build_app_usecases(repository=repo, academic_port=academic, user_port=users, publisher=publisher)

    container = {
        "repo": repo,
        "publisher": publisher,
        "academic": academic,
        "users": users,
    }
    container.update(usecases)
    return container
