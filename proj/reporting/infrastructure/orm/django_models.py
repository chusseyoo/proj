"""Optional ORM model stubs for reporting context.

If reporting re-uses cross-context models (Session, Attendance, Student)
this file can remain empty or contain lightweight proxy models. This
scaffold keeps a placeholder so implementers know where to add orm-related
helpers if needed.
"""
from typing import Any


def get_session_model() -> Any:
    """Return the Session model used by the project (import lazily).

    Example:
        from proj.session.models import Session
        return Session
    """
    raise NotImplementedError("Provide project-specific Session model import here")
