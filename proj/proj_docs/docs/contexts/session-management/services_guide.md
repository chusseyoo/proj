# services_guide.md

Brief: Services orchestrate validation, authorization, and repository access for sessions. Lecturer is required (from auth), and business rules are enforced here.

---

## Conventions

- Inputs validated in services; repositories stay thin
- Lecturer identity comes from JWT (no lecturer_id in request body)
- Cross-context checks delegated to User Management and Academic Structure
- Return DTOs aligned with API contracts

SessionDTO
{
  "session_id": int,
  "program_id": int,
  "course_id": int,
  "lecturer_id": int,
  "stream_id": int | null,
  "time_created": str,   // ISO-8601
  "time_ended": str,     // ISO-8601
  "latitude": str,       // keep as string to preserve precision
  "longitude": str,
  "location_description": str | null,
  "status": "created" | "active" | "ended"
}

SessionService

Dependencies
- SessionRepository
- Academic Structure services (Program, Course, Stream lookups)
- User Management services (Lecturer active and course ownership)
- Event publisher (emit SessionCreated)

Methods
- create_session(auth_lecturer_id, payload)
  - Validate:
    - Lecturer active and assigned to course
    - Program, Course exist; Course belongs to Program
    - Program.has_streams rules (stream null when disabled; if provided, stream belongs to program)
    - time_ended > time_created; duration within 10m..24h
    - No overlap for this lecturer
    - GPS ranges valid
  - Save via repository; emit SessionCreated { program_id, stream_id? }; return DTO with status
- update_session(session_id, auth_lecturer_id, updates)
  - Ownership required; revalidate time window, overlap, and targeting rules
- end_now(session_id, auth_lecturer_id, now)
  - Ownership required; set time_ended = max(now, time_created + min_duration); return DTO
- get_session(session_id, auth_lecturer_id)
  - Ownership required; return DTO with derived status
- list_my_sessions(auth_lecturer_id, filters, page, page_size)
  - Filters: course_id?, program_id?, stream_id?, from_time?, to_time?, status?
  - Compute status from time window; apply pagination; return page payload

Pagination and Responses
- Standard page payload:
{
  "results": [SessionDTO...],
  "total_count": int,
  "page": int,
  "page_size": int,
  "total_pages": int,
  "has_next": bool,
  "has_previous": bool
}

Authorization and Security
- Only lecturers can create/update/end sessions
- Lecturer can access only their own sessions
- Admin (optional) may read across lecturers for support
- Input hardening: validate types, lengths, coordinates, and time windows

Error Model (Domain Exceptions)
- SessionNotFoundError
- AuthorizationError
- LecturerInactiveError
- CourseOwnershipError
- ProgramNotFoundError, CourseNotFoundError, StreamNotFoundError
- ProgramStreamsDisabledError, StreamProgramMismatchError
- InvalidTimeWindowError, OverlappingSessionError
- InvalidCoordinatesError