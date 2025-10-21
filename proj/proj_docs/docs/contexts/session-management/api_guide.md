# api_guide.md

Brief: REST API for Session Management. Lecturer-only creation and management; lecturer inferred from auth token.

---

Conventions
- Base path: /api/session-management/v1
- Auth: Bearer JWT (lecturer role required)
- Content-Type: application/json
- Pagination: page (1-based), page_size (default 20, max 100)
- Errors: consistent envelope with domain codes

Standard error response
{
  "error": { "code": "AuthorizationError", "message": "Only lecturers can create sessions" }
}

SessionDTO
{
  "session_id": 123,
  "program_id": 1,
  "course_id": 301,
  "lecturer_id": 17,
  "stream_id": 25,
  "time_created": "2025-10-25T08:00:00Z",
  "time_ended": "2025-10-25T10:00:00Z",
  "latitude": "-1.28333412",
  "longitude": "36.81666588",
  "location_description": "Room A101",
  "status": "active"
}

Paginated response
{
  "results": [SessionDTO...],
  "total_count": 42,
  "page": 1,
  "page_size": 20,
  "total_pages": 3,
  "has_next": true,
  "has_previous": false
}

Endpoints
- POST /sessions
  - Auth: Lecturer
  - Body: { program_id, course_id, stream_id?, time_created, time_ended, latitude, longitude, location_description? }
  - Notes: lecturer_id from token
  - 201: SessionDTO
  - 400: InvalidTimeWindowError, InvalidCoordinatesError
  - 401/403: AuthorizationError
  - 404: ProgramNotFoundError, CourseNotFoundError, StreamNotFoundError
  - 409: OverlappingSessionError, ProgramStreamsDisabledError, StreamProgramMismatchError

- GET /sessions
  - Auth: Lecturer
  - Query: course_id?, program_id?, stream_id?, from_time?, to_time?, status?, page?, page_size?
  - 200: Paginated list of SessionDTO

- GET /sessions/{session_id}
  - Auth: Lecturer (owner)
  - 200: SessionDTO
  - 403: AuthorizationError
  - 404: SessionNotFoundError

- POST /sessions/{session_id}/end-now
  - Auth: Lecturer (owner)
  - 200: SessionDTO

Admin (optional)
- GET /admin/sessions
  - Auth: Admin
  - 200: Paginated list with same filters

Validation Rules (API layer hints)
- Lecturer-only creation; lecturer_id not accepted in body
- Program required; stream optional but must belong to program
- If program.has_streams=false ⇒ stream must be null
- Course must belong to program; lecturer must be assigned to course and active
- time_ended > time_created; 10m..24h duration
- No overlaps for the lecturer (time ranges)
- latitude in [-90, 90]; longitude in [-180, 180]