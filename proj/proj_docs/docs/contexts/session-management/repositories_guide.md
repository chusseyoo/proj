# repositories_guide.md

Brief: Repository layer for Session Management. Data access for Session with efficient querying and overlap checks.

---

## Structure

- SessionRepository
  - CRUD, queries by lecturer/course/program/stream/time
  - Overlap checks for lecturer time ranges

---

## SessionRepository

Responsibilities:
- Persist and retrieve Session
- Provide overlap detection
- Return ordered querysets for pagination at service/API layers

Methods:

- create(data)
  - Input: { program_id, course_id, lecturer_id, stream_id?, time_created, time_ended, latitude, longitude, location_description? }
  - Behavior: Validates minimal DB-level constraints; business rules handled in service
  - Returns: Session entity

- update(session_id, updates)
  - Allowed: time_created, time_ended, stream_id, latitude, longitude, location_description

- delete(session_id)
  - Hard delete; use only when safe

- get_by_id(session_id)
  - Returns session or raises DoesNotExist

- list_by_lecturer(lecturer_id, from_time?, to_time?)
  - Ordered by time_created DESC

- list_by_course(course_id, from_time?, to_time?)
  - Ordered by time_created DESC

- list_by_program(program_id, stream_id=None, from_time=None, to_time=None)
  - Ordered by time_created DESC

- list_active_by_lecturer(lecturer_id, now)
  - time_created <= now < time_ended

- exists_overlapping_for_lecturer(lecturer_id, start, end, exclude_session_id=None)
  - Overlap logic: (existing_start < end) AND (start < existing_end)

Pagination and Ordering:
- Repositories return ordered QuerySets (time_created DESC)
- Services apply pagination (page, page_size) and map to DTOs

Error Mapping:
- DoesNotExist, IntegrityError bubble up
- Services map to domain exceptions: SessionNotFoundError, InvalidTimeWindowError, OverlappingSessionError, etc.

Optimization Notes:
- Ensure indexes on lecturer_id, course_id, (program_id, stream_id), and time range
- Postgres: consider tstzrange with && operator for overlap checks