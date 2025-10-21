# api_guide.md

Brief: Maintainable, role-aware REST API for Academic Structure. Concise endpoints with clear contracts, minimal surprises, and consistency across Programs, Streams, and Courses.

---

## 1) Conventions

- Base path: /api/academic-structure/v1
- Auth: Bearer JWT (Authorization: Bearer <token>)
- Content-Type: application/json
- Pagination: page (1-based), page_size (default 20, max 100)
- Ordering: ordering=field or -field (where supported)
- DTO keys align with services_guide.md
- Errors: consistent error envelope

Standard paginated response:
```
{
  "results": [...],
  "total_count": 123,
  "page": 1,
  "page_size": 20,
  "total_pages": 7,
  "has_next": true,
  "has_previous": false
}
```

Standard error response:
```
{
  "error": {
    "code": "ProgramNotFoundError",
    "message": "Program not found",
    "details": { "program_id": 999 }
  }
}
```

Roles:
- Admin: full CRUD
- Lecturer: read-only
- Unauthenticated: 401

---

## 2) Programs API

Resource: Program
- DTO:
```
{
  "program_id": 1,
  "program_name": "BSc Computer Science",
  "program_code": "BCS",
  "department_name": "Computer Science",
  "has_streams": true
}
```

Endpoints:
- GET /programs
  - Purpose: List programs (filterable + paginated)
  - Query: department_name, has_streams (true|false), search (name/code), page, page_size, ordering=name|code
  - Auth: Lecturer+ (read)
  - 200: paginated list
- POST /programs
  - Purpose: Create program
  - Body: { program_name, program_code, department_name, has_streams }
  - Auth: Admin (write)
  - 201: Program DTO
  - 409: ProgramCodeAlreadyExistsError
- GET /programs/{program_id}
  - Purpose: Fetch by id
  - Auth: Lecturer+ (read)
  - 200: Program DTO
  - 404: ProgramNotFoundError
- GET /programs/by-code/{program_code}
  - Purpose: Fetch by code (case-insensitive)
  - Auth: Lecturer+ (read)
  - 200/404 as above
- PATCH /programs/{program_id}
  - Purpose: Update mutable fields (name, department_name, has_streams)
  - Auth: Admin
  - 200: Program DTO
  - 400: attempt to change program_code
- DELETE /programs/{program_id}
  - Purpose: Safe delete (no students/courses)
  - Auth: Admin
  - 204: No Content
  - 409: ProgramCannotBeDeletedError

Examples:
- List:
```
GET /api/academic-structure/v1/programs?department_name=Computer%20Science&has_streams=true&page=1&page_size=20
```
- Create:
```
POST /api/academic-structure/v1/programs
{ "program_name": "BSc IT", "program_code": "BIT", "department_name": "IT", "has_streams": false }
```

---

## 3) Streams API

Resource: Stream
- DTO:
```
{
  "stream_id": 25,
  "stream_name": "A",
  "program_id": 1,
  "program_code": "BCS",
  "year_of_study": 2
}
```

Endpoints:
- GET /programs/{program_id}/streams
  - Purpose: List program streams
  - Query: year_of_study (optional), ordering=year_of_study,stream_name
  - Auth: Lecturer+ (read)
  - 200: list of Stream DTOs
- POST /programs/{program_id}/streams
  - Purpose: Create stream under program
  - Body: { stream_name, year_of_study }
  - Auth: Admin
  - 201: Stream DTO
  - 409: StreamAlreadyExistsError
  - 422: StreamNotAllowedError (program.has_streams=false)
- GET /streams/{stream_id}
  - Purpose: Fetch by id
  - Auth: Lecturer+ (read)
  - 200/404
- PATCH /streams/{stream_id}
  - Purpose: Update stream_name/year_of_study
  - Auth: Admin
  - 200: Stream DTO
  - 409: StreamAlreadyExistsError (unique per program/year/name)
- DELETE /streams/{stream_id}
  - Purpose: Safe delete (no students bound)
  - Auth: Admin
  - 204 or 409: StreamCannotBeDeletedError

Examples:
- Create:
```
POST /api/academic-structure/v1/programs/1/streams
{ "stream_name": "Evening", "year_of_study": 3 }
```
- List by year:
```
GET /api/academic-structure/v1/programs/1/streams?year_of_study=2
```

---

## 4) Courses API

Resource: Course
- DTO:
```
{
  "course_id": 301,
  "course_code": "CS201",
  "course_name": "Data Structures",
  "program_id": 1,
  "program_code": "BCS",
  "department_name": "Computer Science",
  "lecturer_id": 17,
  "lecturer_name": "Jane Doe"
}
```

Endpoints:
- GET /courses
  - Purpose: List courses across programs
  - Query: program_id, lecturer_id (nullable), department_name (iexact), q (code/name icontains), page, page_size, ordering=course_code
  - Auth: Lecturer+ (read)
  - 200: paginated list
- POST /courses
  - Purpose: Create course (optional lecturer assignment)
  - Body: { course_code, course_name, program_id, department_name, lecturer_id? }
  - Auth: Admin
  - 201: Course DTO
  - 409: CourseCodeAlreadyExistsError
  - 404: ProgramNotFoundError / LecturerNotFoundError
  - 422: LecturerInactiveError
- GET /courses/{course_id} and GET /courses/by-code/{course_code}
  - Purpose: Fetch single course
  - Auth: Lecturer+ (read)
  - 200/404
- PATCH /courses/{course_id}
  - Purpose: Update course_name/department_name (moving program discouraged)
  - Auth: Admin
  - 200
- POST /courses/{course_id}/assign-lecturer
  - Purpose: Assign lecturer
  - Body: { lecturer_id }
  - Auth: Admin
  - 200: Course DTO
  - 404/422 as above
- POST /courses/{course_id}/unassign-lecturer
  - Purpose: Remove assignment (set NULL)
  - Auth: Admin
  - 200: Course DTO
- DELETE /courses/{course_id}
  - Purpose: Safe delete (no sessions)
  - Auth: Admin
  - 204 or 409: CourseCannotBeDeletedError

Examples:
- Create:
```
POST /api/academic-structure/v1/courses
{ "course_code": "CS205", "course_name": "Algorithms", "program_id": 1, "department_name": "Computer Science" }
```
- Assign lecturer:
```
POST /api/academic-structure/v1/courses/301/assign-lecturer
{ "lecturer_id": 17 }
```

---

## 5) Validation Rules (API layer hints)

- program_code: uppercase, 2–6 chars, alnum; immutable after create.
- course_code: uppercase pattern ^[A-Z]{2,6}[0-9]{2,4}$; immutable after create.
- stream_name: 1–50 chars; unique per (program, year, name).
- year_of_study: integer 1..4.
- program.has_streams=false → block stream creation.
- Lecturer assignment:
  - lecturer_id refers to LecturerProfile.id
  - Lecturer's User must be active

Return 400 for shape/type errors, 404 for missing resources, 409 for uniqueness/safe-delete conflicts, 422 for semantic constraints (e.g., StreamNotAllowed, LecturerInactive).

---

## 6) Security

- Auth: JWT Bearer on all endpoints.
- RBAC:
  - Admin: POST/PATCH/DELETE allowed.
  - Lecturer: GET only.
- Input hardening: validate types, lengths, enums; reject unknown fields.

---

## 7) Integration Notes

- User Management:
  - Resolve lecturer_id → LecturerProfile; enrich lecturer_name from related User.
- Session Management:
  - Block course delete if sessions exist (can_be_deleted check).
- Consistency:
  - Services enforce business rules; repositories ensure data integrity.

