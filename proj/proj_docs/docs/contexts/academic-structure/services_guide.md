# services_guide.md

Brief: Comprehensive, maintainable guide for implementing the service layer in Academic Structure. Each service is grouped with its methods, validations, transactions, errors, and testing. Keep services thin (business orchestration), repositories for data access.

---

## File Organization

Service Layer Structure:
```
academic_structure/
├── services/
│   ├── __init__.py
│   ├── program_service.py   # ProgramService
│   ├── stream_service.py    # StreamService
│   └── course_service.py    # CourseService
├── repositories/
│   ├── program_repository.py
│   ├── stream_repository.py
│   └── course_repository.py
├── models.py
└── ...
```

Conventions:
- Dependency injection: pass repositories into service constructors for easy testing.
- DTOs: return simple dicts from services when consumed by APIs.
- Authorization: enforce role-based permissions in services (Admin/DeptHead).
- Pagination: services accept page/page_size and return a standard page payload.

---

# PART 1: PROGRAM SERVICE

## 1.1 ProgramService Overview
- Purpose: Manage Programs (create, update, list, delete with safety checks).
- File: services/program_service.py
- Depends on: ProgramRepository, StreamRepository (for info), CourseRepository (for delete checks).
- Typical Callers: Admin/DeptHead workflows, UI for catalogs.

## 1.2 DTOs (shapes returned by services)
- ProgramDTO:
  ```
  {
    "program_id": int,
    "program_name": str,
    "program_code": str,     # uppercase, unique (e.g., "BCS")
    "department_name": str,
    "has_streams": bool
  }
  ```

## 1.3 Methods

1) create_program(data)
- Purpose: Add a new program.
- Input: data = { program_name, program_code, department_name, has_streams }
- Validations:
  - program_code: exactly 3 uppercase letters (e.g., BCS, BEG, DIT); unique.
  - program_name: 5-200 chars.
  - department_name: 5-50 chars.
- Flow:
  - Check code uniqueness → normalize code to uppercase → create via repository.
- Returns: ProgramDTO
- Errors: ProgramCodeAlreadyExistsError, ValidationError
- Transaction: Not required.

2) update_program(program_id, updates)
- Purpose: Update name/department/has_streams (not code).
- Allowed fields: program_name, department_name, has_streams (code immutable).
- Validations: same length rules as create; disallow program_code change.
- Flow: fetch → validate → update → return DTO.
- Errors: ProgramNotFoundError, ValidationError
- Transaction: Not required.

3) delete_program(program_id)
- Purpose: Safely delete a program.
- Safety: Must have no enrolled students and no courses (streams may cascade).
- Flow: can_be_deleted() via repository → if False, raise ProgramCannotBeDeletedError → delete.
- Returns: None
- Errors: ProgramNotFoundError, ProgramCannotBeDeletedError
- Transaction: Optional (simple single delete).

4) get_program_by_id(program_id)
- Purpose: Fetch one program.
- Returns: ProgramDTO
- Errors: ProgramNotFoundError

5) get_program_by_code(program_code)
- Purpose: Fetch by code (case-insensitive).
- Returns: ProgramDTO
- Errors: ProgramNotFoundError

6) list_programs(filters=None, page=None, page_size=None)
- Purpose: List programs, optionally filtered and paginated.
- Common filters: department_name, has_streams (bool).
- Returns: Page payload or list of ProgramDTOs:
  ```
  { "results": [ProgramDTO...], "total_count": int, "page": int, "page_size": int, "total_pages": int }
  ```
- Notes: Use repository ordering by program_name.

7) list_programs_with_streams()/list_programs_without_streams()
- Purpose: Convenience lists for UIs.
- Returns: List of ProgramDTOs.

## 1.4 Error Handling (map repository → domain)
- Program.DoesNotExist → ProgramNotFoundError
- IntegrityError (duplicate code) → ProgramCodeAlreadyExistsError
- Unsafe delete → ProgramCannotBeDeletedError

---

# PART 2: STREAM SERVICE

## 2.1 StreamService Overview
- Purpose: Manage Streams per Program/year.
- File: services/stream_service.py
- Depends on: StreamRepository, ProgramRepository (has_streams check).
- Typical Callers: Admin/DeptHead, student placement workflows.

## 2.2 DTOs
- StreamDTO:
  ```
  {
    "stream_id": int,
    "stream_name": str,        # e.g., "A", "Evening", "SE-A"
    "program_id": int,
    "program_code": str,       # optional enrichment
    "year_of_study": int       # 1..4
  }
  ```

## 2.3 Methods

1) create_stream(program_id, stream_name, year_of_study)
- Purpose: Add a stream under a program and year.
- Preconditions: Program.has_streams must be True.
- Validations:
  - year_of_study in 1..4.
  - stream_name: 1-50 chars; unique per (program, year, name).
- Flow:
  - Fetch program → if has_streams=False → StreamNotAllowedError → dedupe via exists_by_program_and_name → create.
- Returns: StreamDTO
- Errors: ProgramNotFoundError, StreamNotAllowedError, StreamAlreadyExistsError, ValidationError
- Transaction: Not required.

2) update_stream(stream_id, updates)
- Purpose: Rename stream or adjust year.
- Allowed fields: stream_name, year_of_study.
- Validations: uniqueness in new (program, year, name), year range 1..4.
- Returns: StreamDTO
- Errors: StreamNotFoundError, StreamAlreadyExistsError, ValidationError

3) delete_stream(stream_id)
- Purpose: Safely delete stream.
- Safety: Must have no students assigned.
- Flow: can_be_deleted(stream_id) → if False raise StreamCannotBeDeletedError → delete.
- Returns: None
- Errors: StreamNotFoundError, StreamCannotBeDeletedError

4) get_stream(stream_id)
- Purpose: Fetch one stream, enriched with program code/name when needed.
- Returns: StreamDTO
- Errors: StreamNotFoundError

5) list_streams_by_program(program_id, year_of_study=None)
- Purpose: List streams for program, optionally filtered by year.
- Returns: [StreamDTO]
- Notes: Order by year_of_study, stream_name.

## 2.4 Error Handling
- Stream.DoesNotExist → StreamNotFoundError
- IntegrityError (unique_together) → StreamAlreadyExistsError
- has_streams=False → StreamNotAllowedError
- Students exist → StreamCannotBeDeletedError

---

# PART 3: COURSE SERVICE

## 3.1 CourseService Overview
- Purpose: Manage Courses (assignment to programs and lecturers).
- File: services/course_service.py
- Depends on: CourseRepository, ProgramRepository
- Cross-Context: User Management for Lecturer validation; Session Management for safe deletion.
- Typical Callers: Admin/DeptHead (manage catalog), Lecturers (view assignments).

## 3.2 DTOs
- CourseDTO:
  ```
  {
    "course_id": int,
    "course_code": str,         # e.g., "CS201" (uppercase)
    "course_name": str,
    "program_id": int,
    "program_code": str,        # optional enrichment
    "department_name": str,
    "lecturer_id": int | null,  # LecturerProfile ID (nullable)
    "lecturer_name": str | null # e.g., "John Doe" (optional enrichment)
  }
  ```

## 3.3 Methods

1) create_course(data)
- Purpose: Add new course; lecturer assignment optional at creation.
- Input:
  - course_name (3-200), course_code (pattern), program_id, department_name (5-50), lecturer_id? (optional)
- Validations:
  - course_code: exactly 6 uppercase alphanumeric characters (e.g., BCS012, BEG230, DIT410); unique.
  - department_name: 5-50 chars.
  - program exists.
  - If lecturer_id provided: lecturer exists and user.is_active=True (User Management).
  - Optional business rule: department_name should match lecturer.department_name (warn or enforce).
- Flow:
  - Normalize course_code uppercase → check uniqueness → validate foreign keys → create.
- Returns: CourseDTO
- Errors: CourseCodeAlreadyExistsError, ProgramNotFoundError, LecturerNotFoundError, LecturerInactiveError, ValidationError
- Transaction: Not required.

2) update_course(course_id, updates)
- Purpose: Update name/department/lecturer; course_code typically immutable.
- Allowed: course_name, department_name; optionally move program_id (discouraged).
- Lecturer updates should use assign/unassign methods instead.
- Returns: CourseDTO
- Errors: CourseNotFoundError, ValidationError

3) assign_lecturer(course_id, lecturer_id)
- Purpose: Assign a lecturer to a course.
- Validations:
  - Lecturer exists and is active (User Management).
  - Optional: Department alignment between course and lecturer.
- Flow:
  - Cross-context validate → repository.assign_lecturer → return updated DTO.
- Errors: CourseNotFoundError, LecturerNotFoundError, LecturerInactiveError, ValidationError
- Transaction: Not required (single update).

4) unassign_lecturer(course_id)
- Purpose: Remove lecturer assignment (set NULL).
- Returns: CourseDTO
- Errors: CourseNotFoundError

5) delete_course(course_id)
- Purpose: Safely delete course.
- Safety: Must have no sessions (Session Management).
- Flow: can_be_deleted(course_id) → if False raise CourseCannotBeDeletedError → delete.
- Returns: None
- Errors: CourseNotFoundError, CourseCannotBeDeletedError
- Transaction: Optional.

6) get_course_by_id(course_id) / get_course_by_code(course_code)
- Purpose: Fetch single course; enrich with program and lecturer names when needed.
- Returns: CourseDTO
- Errors: CourseNotFoundError

7) list_courses(filters=None, page=None, page_size=None)
- Common filters: program_id, lecturer_id (nullable), department_name (iexact), code/name search (icontains).
- Returns: Page payload or list of CourseDTOs.
- Optimization: select_related('program', 'lecturer__user') in repository.

## 3.4 Cross-Context Integration
- User Management:
  - Validate lecturer exists/active before assignment.
  - Enrich lecturer_name via lecturer.user.get_full_name().
- Session Management:
  - Block delete when sessions exist (repository can_be_deleted).
  - Optionally unassign lecturer when deactivated in User Management (handled by UM services).

## 3.5 Error Handling
- Course.DoesNotExist → CourseNotFoundError
- Duplicate code → CourseCodeAlreadyExistsError
- Sessions exist on delete → CourseCannotBeDeletedError
- Lecturer checks → LecturerNotFoundError, LecturerInactiveError

---

# PART 4: AUTHORIZATION AND SECURITY

- Default Policy:
  - Admin/DeptHead: can create/update/delete Programs, Streams, Courses.
  - Lecturer: read-only on Programs/Streams; list/view Courses; cannot mutate catalog.
- Email/ID Validation:
  - Delegate lecturer validation to User Management services.
- Data Consistency:
  - Use repository constraints (unique codes, composite uniqueness for streams).

---

# PART 5: TRANSACTION MANAGEMENT

- When to use @transaction.atomic:
  - Bulk operations (e.g., bulk import of courses or streams).
  - Chained mutations that must succeed together (rare in this context).
- Avoid long transactions:
  - Do not send emails or call external services inside transactions.
- Typical operations here are single-record mutations; transactions are optional except for bulk flows.

---

# PART 6: PAGINATION AND RESPONSES

Standard page payload:
```
{
  "results": [DTO...],
  "total_count": int,
  "page": int,
  "page_size": int,
  "total_pages": int,
  "has_next": bool,
  "has_previous": bool
}
```
Guidelines:
- Apply consistent ordering (Programs by name, Streams by year then name, Courses by code).
- Limit page_size with a sane max (e.g., 100).

---

# PART 7: ERROR MODEL (DOMAIN EXCEPTIONS)

Define in a shared module (e.g., academic_structure/services/errors.py):
- ProgramNotFoundError, ProgramCodeAlreadyExistsError, ProgramCannotBeDeletedError
- StreamNotFoundError, StreamAlreadyExistsError, StreamNotAllowedError, StreamCannotBeDeletedError
- CourseNotFoundError, CourseCodeAlreadyExistsError, CourseCannotBeDeletedError
- LecturerNotFoundError, LecturerInactiveError
Mapping:
- Repositories raise DoesNotExist/IntegrityError → Services map to domain exceptions with clear messages.

---

# PART 8: MAINTAINABILITY NOTES

- Single Responsibility: Keep each service focused; avoid cross-context repository calls in repositories—do them in services.
- Testability: Services accept repositories via constructor; mock in unit tests.
- Immutability: Treat program_code and course_code as immutable after creation (documented rule).
- Naming Consistency: Keep DTO keys aligned with API contracts.
- Logging: Log creates/updates/deletes at INFO; validation failures at WARNING.

---

# PART 9: EXAMPLES (BRIEF FLOWS)

- Assign Lecturer to Course (happy path):
  1) Validate course exists.
  2) UM: fetch lecturer; ensure active.
  3) Assign via repository.
  4) Return CourseDTO with lecturer_name.

- Create Stream under Program:
  1) Fetch program; ensure has_streams=True.
  2) Check unique (program, year, name).
  3) Create via repository.
  4) Return StreamDTO.

-