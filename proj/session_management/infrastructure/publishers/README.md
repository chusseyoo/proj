Event Publishers
================

This folder contains event publisher implementations for different environments.

Files
-----

- `in_memory_publisher.py`: Test-friendly publisher that records events in memory
- `celery_publisher.py`: Production publisher that enqueues Celery tasks
- `utils.py`: Helper functions for safe event publishing (transaction.on_commit)

In-Memory Publisher (Testing)
------------------------------

Use for unit and integration tests:

```python
from session_management.infrastructure.publishers.in_memory_publisher import InMemoryPublisher

publisher = InMemoryPublisher()
# ... execute use-case ...
assert len(publisher.events) == 1
assert publisher.events[0]["event"] == "session.created"
```

Celery Publisher (Production)
------------------------------

Use in production to enqueue async tasks:

```python
from session_management.infrastructure.publishers.celery_publisher import CeleryPublisher

publisher = CeleryPublisher()
# Events are enqueued as Celery tasks for async processing
```

Publishing After Commit
------------------------

Always use `publish_after_commit()` to ensure events are only published after successful DB commits:

```python
from session_management.infrastructure.publishers.utils import publish_after_commit

# In a use-case
saved = session_repository.save(domain_session)
publish_after_commit(
    publisher,
    "session.created",
    {"session_id": saved.session_id, "lecturer_id": saved.lecturer_id}
)
```

This prevents publishing events for transactions that later rollback.
