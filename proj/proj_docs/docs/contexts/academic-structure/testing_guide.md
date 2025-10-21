# testing_guide.md

Brief: Focused testing strategy for Academic Structure context. This document keeps Parts 1-6 and 8 (models, repositories, services, API, integration, edge cases, fixtures) and removes performance, test organization, and CI/CD content.

---

## File Organization

Testing Structure:
```
academic_structure/
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_repositories.py
│   ├── test_services.py
│   ├── test_api.py
│   ├── fixtures.py
│   └── conftest.py
```

Conventions:
- Pytest + Django test DB
- Mock cross-context dependencies where appropriate
- Use fixtures/factory patterns in fixtures.py
- Mark integration tests with @pytest.mark.integration

---

# PART 1: MODEL TESTS

Purpose: Validate model field constraints, methods, and DB-level rules.

Key tests (test_models.py):
- Program: creation, uppercase code enforcement, uniqueness, validation pattern, __str__.
- Stream: creation, unique_together (program/year/name), year_of_study range, cascade delete, __str__.
- Course: creation with/without lecturer, code uppercase & pattern, uniqueness, cascade behavior, set-null on lecturer delete, __str__.

Fixtures: program_with_streams, program_without_streams, stream_year_2, lecturer_profile, course_without_lecturer.

---

# PART 2: REPOSITORY TESTS

Purpose: Validate data access methods, query behavior, and safety checks.

Key tests (test_repositories.py):
- ProgramRepository: create, get_by_id, get_by_code (case-insensitive), exists_by_code, list_all, list_with_streams, update, delete, can_be_deleted checks (courses/students).
- StreamRepository: create, get_by_id, exists_by_program_and_name, list_by_program (optional year filter), update, delete, can_be_deleted (students).
- CourseRepository: create (with/without lecturer), get_by_id (select_related), get_by_code (case-insensitive), exists_by_code, list_by_program, list_by_lecturer (including null), assign/unassign lecturer, update, delete, can_be_deleted (sessions).

Repository test patterns:
- Use @pytest.mark.django_db
- Assert repository methods call DB as expected
- Mock external calls (Session Management) for can_be_deleted

---

# PART 3: SERVICE TESTS

Purpose: Validate business logic, orchestrations, validation, and cross-context interactions; use mocks for repos and external services.

Key tests (test_services.py):
- ProgramService: create (normalizes code, uniqueness), update (disallow code change), delete (safety), list with pagination.
- StreamService: create (requires program.has_streams), duplicate checks, update validation, delete safety.
- CourseService: create (validate program and optional lecturer active), assign/unassign lecturer (validate UM), delete safety (sessions blocking).

Mocking pattern:
- Inject mock repositories into services
- Use unittest.mock for external services (User Management, Session Management)
- Verify exceptions map to domain errors

---

# PART 4: API TESTS

Purpose: Test HTTP endpoints, auth, authorization, request/response shapes and status codes.

Key tests (test_api.py):
- Programs endpoints: list (auth), filters, create (admin vs lecturer), get by id, get by code, patch (prevent code change), delete (safe delete).
- Streams endpoints: list by program, create (program.has_streams enforcement), update, delete (student blocking).
- Courses endpoints: list, create (with/without lecturer), assign/unassign lecturer, delete (session blocking).

API test patterns:
- Use DRF APIClient or Django test Client with JWT tokens from User Management fixtures
- Separate unit vs integration API tests (mark integration for cross-context)

---

# PART 5: INTEGRATION TESTS

Purpose: End-to-end flows across contexts (real DB, real or test implementations for UM/Session).

Key integration scenarios:
- Assigning a lecturer (create LecturerProfile in UM, assign in Academic Structure, verify behavior on deactivate)
- Course deletion blocked by Session entries (create session in Session Management)
- Stream deletion blocked by students assigned (create StudentProfile in UM)
- Program deletion cascade behavior with streams/courses

Guidelines:
- Keep integration tests focused and limited in number
- Mark with @pytest.mark.integration and run separately in CI

---

# PART 6: EDGE CASE TESTS

Purpose: Boundary conditions and null handling.

Important cases:
- Program/course/stream min/max lengths and code boundaries
- Year_of_study boundaries (1..4)
- Null lecturer handling (create/fetch with lecturer NULL)
- Pagination edge pages (partial last page)
- Empty DB responses

---

# PART 8: TEST DATA MANAGEMENT (FIXTURES & FACTORIES)

Purpose: Reusable fixtures and optional factory definitions to speed test authoring.

Contents of fixtures.py:
- Program fixtures: programs_set (with/without streams)
- Stream fixtures: streams_for_bcs
- Lecturer fixtures: active_lecturer, inactive_lecturer (create User + LecturerProfile)
- Course fixtures: courses_for_bcs

Optional factories (factory_boy) for scalable test data:
- ProgramFactory, StreamFactory, CourseFactory (recommended for bulk tests)

Example fixture snippet:
```python
@pytest.fixture
def active_lecturer():
    user = User.objects.create(email="active@example.com", role="Lecturer", is_active=True)
    return LecturerProfile.objects.create(user=user, department_name="Computer Science")
```
