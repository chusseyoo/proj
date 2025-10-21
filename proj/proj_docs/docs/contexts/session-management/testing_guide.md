# testing_guide.md

Brief: Focused testing strategy for Session Management. Includes Parts 1–6 and 8 (models, repositories, services, API, integration, edge cases, fixtures).

---

File Organization
```
session_management/
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_repositories.py
│   ├── test_services.py
│   ├── test_api.py
│   ├── fixtures.py
│   └── conftest.py
```

Conventions
- pytest + Django test DB
- Mock cross-context services (UM, Academic Structure)
- Use fixtures for lecturer, program, course, stream
- Mark integration tests with @pytest.mark.integration

PART 1: MODEL TESTS
- Session: creation (with lecturer required), time window check (ended > created), GPS bounds, stream nullable, derived status logic (helper), on_delete behaviors (PROTECT lecturer, CASCADE course/program, SET_NULL stream)

PART 2: REPOSITORY TESTS
- create/get/update/delete
- list_by_lecturer/course/program with ordering (time_created DESC)
- exists_overlapping_for_lecturer (positive/negative, exclude_session_id)
- list_active_by_lecturer(now)

PART 3: SERVICE TESTS
- create_session: validates lecturer active and owns course; program/course exist; course in program; streams rules; time window; overlap; GPS
- update_session: ownership and revalidation
- end_now: ownership and minimum duration enforcement
- get_session: ownership
- list_my_sessions: filters and pagination

PART 4: API TESTS
- POST /sessions: 201 on success; 403 non-lecturer; 404 invalid FKs; 409 overlap; 400 invalid time/GPS
- GET /sessions: filtering and pagination
- GET /sessions/{id}: ownership
- POST /sessions/{id}/end-now: ownership

PART 5: INTEGRATION TESTS
- CourseOwnership: lecturer not assigned to course → blocked
- Program-Stream consistency: stream not in program → blocked
- Program.has_streams=false with stream provided → blocked
- Session overlaps across same lecturer → blocked

PART 6: EDGE CASE TESTS
- Minimum duration (10 minutes) and maximum duration (24 hours)
- Boundary coordinates (-90/90, -180/180)
- Stream null vs provided when has_streams=True
- List with empty DB (pagination zero results)

PART 8: FIXTURES
- Lecturer (active/inactive) with User Management
- Program (has_streams True/False), Stream (belongs to program)
- Course (belongs to program, assigned lecturer)
- Helper to generate time windows (now, now+30m, etc.)