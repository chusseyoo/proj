In-memory publisher
===================

This folder contains a simple, test-friendly publisher implementation:

- `in_memory_publisher.py`: Implements `EventPublisherPort.publish(event_name, payload)` and records published events to an in-memory `events` list.

When to use
-----------
- Unit and integration tests that need to assert the application published events (for example, `session.created`).
- Local development when you don't want to depend on external message brokers or task queues.

How it works
------------
- Create an instance and inject it into application use-cases which accept a `publisher` argument.
- After executing the use-case, inspect `publisher.events` to see recorded events. Each event entry is a dict with keys `event` and `payload`.

Safety
------
- The in-memory publisher is intentionally non-blocking and does not send network traffic. Use it only for local/testing scenarios. Replace with a real adapter (Rabbit, Kafka, Celery, etc.) in production.
