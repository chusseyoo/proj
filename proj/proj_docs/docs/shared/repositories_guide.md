# Repository Layer Guide - Complete System Data Access Architecture

**Last Updated**: October 21, 2025  
**Purpose**: Comprehensive overview of all repository patterns and data access strategies across bounded contexts

---

## Overview

This document provides a system-wide view of all repositories across bounded contexts. Repositories encapsulate data access logic, abstract persistence mechanisms, provide query interfaces, and maintain the boundary between domain/application layers and infrastructure.

---

## System-Wide Repository Conventions

### Repository Pattern Principles
1. **Encapsulation**: Hide persistence details from services
2. **Collection Interface**: Treat repositories as in-memory collections
3. **Single Responsibility**: One repository per aggregate root
4. **Query Optimization**: Efficient queries with appropriate indexes and eager loading
5. **Error Translation**: Map DB errors to domain exceptions

### Standard Repository Structure
```
{Entity}Repository
├── CRUD Operations
│   ├── create(data) → Entity
│   ├── get_by_id(id) → Entity | DoesNotExist
│   ├── update(id, data) → Entity
│   ├── delete(id) → void
├── Query Methods
│   ├── list_all(filters?, page?, page_size?) → QuerySet[Entity]
│   ├── exists_by_{field}(value) → bool
│   ├── get_by_{field}(value) → Entity | DoesNotExist
├── Specialized Queries
│   └── Context-specific queries
└── Helper Methods
    └── Validation, counting, aggregation
```

### Common Patterns

**Pagination**
```python
# Standard pagination parameters
page: int = 1  # 1-based
page_size: int = 20  # default 20, max 100
offset = (page - 1) * page_size
queryset.offset(offset).limit(page_size)
```

**Ordering**
```python
# Default: most recent first (created_at DESC or similar)
queryset.order_by('-created_at')
```

**Eager Loading**
```python
# Use select_related for ForeignKey (1-to-1, many-to-1)
queryset.select_related('user', 'course')

# Use prefetch_related for ManyToMany or reverse ForeignKey
queryset.prefetch_related('students', 'enrollments')
```

**Error Handling**
```python
# Map Django ORM errors to domain exceptions
try:
    entity = Model.objects.get(id=id)
except Model.DoesNotExist:
    raise EntityNotFoundError(f"{Model.__name__} with id {id} not found")
except IntegrityError as e:
    raise DomainIntegrityError(str(e))
```

---

## Repositories by Bounded Context

### 1. User Management

**Base Path**: `user_management/infrastructure/repositories/`

#### UserRepository

**Purpose**: Manage User entity persistence and queries

**CRUD Operations**
- `create(email, password_hash, role, is_active)` → User
  - Validates email uniqueness
  - Returns User entity
- `get_by_id(user_id)` → User | UserNotFoundError
- `update(user_id, updates)` → User
  - Allowed fields: email, is_active, role
- `delete(user_id)` → void
  - Soft delete (set is_active=False) or hard delete based on policy

**Query Methods**
- `get_by_email(email)` → User | UserNotFoundError
  - Case-insensitive lookup
- `exists_by_email(email)` → bool
  - Used for duplicate checking during registration
- `list_by_role(role, page, page_size)` → QuerySet[User]
  - Filter by role (Student, Lecturer, Admin)
- `list_active_users(filters, page, page_size)` → QuerySet[User]
  - Filter: is_active=True

**Indexes**
- UNIQUE: email (case-insensitive)
- INDEX: role
- INDEX: is_active

**Priority**: CRITICAL (authentication foundation)

**Reference**: [`docs/contexts/user-management/repositories_guide.md`](docs/contexts/user-management/repositories_guide.md)

---

#### StudentProfileRepository

**Purpose**: Manage StudentProfile entity persistence

**CRUD Operations**
- `create(user_id, student_id, program_id, stream_id?, enrollment_date)` → StudentProfile
- `get_by_id(profile_id)` → StudentProfile
- `get_by_user_id(user_id)` → StudentProfile
- `update(profile_id, updates)` → StudentProfile
- `delete(profile_id)` → void (CASCADE on user delete)

**Query Methods**
- `get_by_student_id(student_id)` → StudentProfile
  - QR code validation uses this
- `exists_by_student_id(student_id)` → bool
- `list_by_program(program_id, stream_id?, page, page_size)` → QuerySet[StudentProfile]
  - Eligibility queries for sessions/reporting
  - Filter by stream if provided
- `count_by_program(program_id, stream_id?)` → int

**Indexes**
- UNIQUE: student_id
- UNIQUE: user_id (1-to-1)
- INDEX: (program_id, stream_id)

**Priority**: CRITICAL (attendance and reporting depend on this)

---

#### LecturerProfileRepository

**Purpose**: Manage LecturerProfile entity persistence

**CRUD Operations**
- `create(user_id, department, office_location?)` → LecturerProfile
- `get_by_id(profile_id)` → LecturerProfile
- `get_by_user_id(user_id)` → LecturerProfile
- `update(profile_id, updates)` → LecturerProfile

**Query Methods**
- `list_by_department(department, page, page_size)` → QuerySet[LecturerProfile]
- `list_active_lecturers(page, page_size)` → QuerySet[LecturerProfile]
  - Joins with User (is_active=True)

**Indexes**
- UNIQUE: user_id (1-to-1)
- INDEX: department

**Priority**: HIGH

---

### 2. Academic Structure

**Base Path**: `academic_structure/infrastructure/repositories/`

#### ProgramRepository

**Purpose**: Manage Program entity persistence

**CRUD Operations**
- `create(code, name, has_streams)` → Program
  - Enforces uppercase code
- `get_by_id(program_id)` → Program
- `get_by_code(code)` → Program
  - Case-insensitive lookup
- `update(program_id, updates)` → Program
  - Cannot update code (business rule)
- `delete(program_id)` → void
  - Checks for dependent courses/students via `can_be_deleted()`

**Query Methods**
- `exists_by_code(code)` → bool
- `list_all(page, page_size)` → QuerySet[Program]
- `list_with_streams(page, page_size)` → QuerySet[Program]
  - Filter: has_streams=True
  - Prefetch related streams
- `can_be_deleted(program_id)` → bool
  - Checks for courses (via CourseRepository) and students (via StudentProfileRepository)

**Indexes**
- UNIQUE: code (case-insensitive)

**Priority**: HIGH

**Reference**: [`docs/contexts/academic-structure/repositories_guide.md`](docs/contexts/academic-structure/repositories_guide.md)

---

#### StreamRepository

**Purpose**: Manage Stream entity persistence

**CRUD Operations**
- `create(program_id, name, year_of_study)` → Stream
- `get_by_id(stream_id)` → Stream
- `update(stream_id, updates)` → Stream
- `delete(stream_id)` → void
  - Checks for students via `can_be_deleted()`

**Query Methods**
- `exists_by_program_and_name(program_id, name, year_of_study)` → bool
  - Unique constraint enforcement
- `list_by_program(program_id, year_of_study?, page, page_size)` → QuerySet[Stream]
  - Optional year filter
  - Order by year_of_study, name
- `can_be_deleted(stream_id)` → bool
  - Checks for students (via StudentProfileRepository)

**Indexes**
- UNIQUE: (program_id, name, year_of_study)
- INDEX: program_id

**Priority**: MEDIUM

---

#### CourseRepository

**Purpose**: Manage Course entity persistence

**CRUD Operations**
- `create(code, name, program_id, lecturer_id?)` → Course
  - Enforces uppercase code
- `get_by_id(course_id)` → Course
  - select_related('lecturer', 'program')
- `get_by_code(code)` → Course
  - Case-insensitive
- `update(course_id, updates)` → Course
- `delete(course_id)` → void
  - Checks for sessions via `can_be_deleted()`

**Query Methods**
- `exists_by_code(code)` → bool
- `list_by_program(program_id, page, page_size)` → QuerySet[Course]
- `list_by_lecturer(lecturer_id, page, page_size)` → QuerySet[Course]
  - Includes courses with lecturer_id=NULL if requested
- `assign_lecturer(course_id, lecturer_id)` → Course
- `unassign_lecturer(course_id)` → Course
  - Set lecturer_id=NULL
- `can_be_deleted(course_id)` → bool
  - Checks for sessions (via SessionRepository in Session Management context)

**Indexes**
- UNIQUE: code (case-insensitive)
- INDEX: program_id
- INDEX: lecturer_id

**Priority**: HIGH

---

### 3. Session Management

**Base Path**: `session_management/infrastructure/repositories/`

#### SessionRepository

**Purpose**: Manage Session entity persistence

**CRUD Operations**
- `create(program_id, course_id, lecturer_id, stream_id?, time_created, time_ended, latitude, longitude, location_description?)` → Session
- `get_by_id(session_id)` → Session
  - select_related('program', 'course', 'lecturer', 'stream')
- `update(session_id, updates)` → Session
  - Allowed: time_created, time_ended, stream_id, location_description
- `delete(session_id)` → void

**Query Methods**
- `list_by_lecturer(lecturer_id, from_time?, to_time?, page, page_size)` → QuerySet[Session]
  - Order by time_created DESC
- `list_by_course(course_id, from_time?, to_time?, page, page_size)` → QuerySet[Session]
- `list_by_program(program_id, stream_id?, from_time?, to_time?, page, page_size)` → QuerySet[Session]
- `list_active_by_lecturer(lecturer_id, now)` → QuerySet[Session]
  - time_created <= now < time_ended
- `exists_overlapping_for_lecturer(lecturer_id, start, end, exclude_session_id?)` → bool
  - Overlap logic: (existing_start < end) AND (start < existing_end)
  - Used to prevent lecturer double-booking

**Indexes**
- INDEX: lecturer_id
- INDEX: course_id
- INDEX: (program_id, stream_id)
- INDEX: (time_created, time_ended) - for range queries

**Optimization**
- PostgreSQL: Use tstzrange type with && operator for efficient overlap checks
- MySQL: Use BETWEEN for time range queries

**Priority**: CRITICAL (core workflow)

**Reference**: [`docs/contexts/session-management/repositories_guide.md`](docs/contexts/session-management/repositories_guide.md)

---

### 4. Attendance Recording

**Base Path**: `attendance_recording/infrastructure/repositories/`

#### AttendanceRepository

**Purpose**: Manage Attendance entity persistence

**CRUD Operations**
- `create(student_profile_id, session_id, latitude, longitude, status, is_within_radius)` → Attendance
  - Enforces UNIQUE (student_profile_id, session_id)
- `get_by_id(attendance_id)` → Attendance
  - select_related('student_profile', 'session')

**Query Methods**
- `exists_for_student_and_session(student_profile_id, session_id)` → bool
  - **CRITICAL**: Duplicate prevention
  - Used before creating attendance
- `list_by_session(session_id, page, page_size)` → QuerySet[Attendance]
  - Order by time_recorded DESC
- `list_by_student(student_profile_id, from_date?, to_date?, page, page_size)` → QuerySet[Attendance]
  - Optional date range filter
- `count_by_session(session_id)` → int
- `count_by_student(student_profile_id)` → int

**Statistics Queries**
- `get_session_statistics(session_id)` → dict
  - Returns: { present_count, late_count, absent_count, total_eligible }
  - Used by Reporting context
- `get_student_attendance_rate(student_profile_id, from_date, to_date)` → float
  - Returns: percentage (0-100)

**Indexes**
- UNIQUE: (student_profile_id, session_id)
- INDEX: session_id
- INDEX: student_profile_id
- INDEX: time_recorded

**Priority**: CRITICAL (immutable records, duplicate prevention)

**Reference**: [`docs/contexts/attendance-recording/repositories_guide.md`](docs/contexts/attendance-recording/repositories_guide.md)

---

### 5. Email Notifications

**Base Path**: `email_notifications/infrastructure/repositories/`

#### EmailNotificationRepository

**Purpose**: Manage EmailNotification entity persistence

**CRUD Operations**
- `create(session_id, student_profile_id, token, status, email_body)` → EmailNotification
- `bulk_create(notifications: list[dict])` → list[EmailNotification]
  - **HIGH PRIORITY**: Efficient bulk inserts (1 query vs N queries)
  - Used when generating notifications for entire class
- `get_by_id(notification_id)` → EmailNotification
- `update_status(notification_id, status, sent_at?, error_message?)` → EmailNotification

**Query Methods**
- `get_by_token(token)` → EmailNotification
  - Used by Attendance Recording to validate tokens
- `list_pending(page, page_size)` → QuerySet[EmailNotification]
  - Filter: status='pending'
  - Order by created_at ASC (FIFO)
- `list_failed(page, page_size)` → QuerySet[EmailNotification]
  - Filter: status='failed'
  - For admin retry interface
- `list_by_session(session_id, page, page_size)` → QuerySet[EmailNotification]
- `list_by_student(student_profile_id, page, page_size)` → QuerySet[EmailNotification]

**Bulk Operations**
- `bulk_update_status(notification_ids: list[int], status, sent_at?, error_message?)` → int
  - Returns: count of updated records

**Indexes**
- UNIQUE: (session_id, student_profile_id)
- UNIQUE: token
- INDEX: status
- INDEX: session_id
- INDEX: student_profile_id
- INDEX: created_at

**Priority**: HIGH (performance critical for bulk operations)

**Reference**: [`docs/contexts/email-notifications/repositories_guide.md`](docs/contexts/email-notifications/repositories_guide.md)

---

### 6. Reporting

**Base Path**: `reporting/infrastructure/repositories/`

#### ReportRepository

**Purpose**: Manage Report entity persistence and cross-context data aggregation

**CRUD Operations**
- `create(session_id, generated_by_id, file_path?, file_type?)` → Report
- `get_by_id(report_id)` → Report
  - select_related('session', 'generated_by')
- `update_export_details(report_id, file_path, file_type)` → Report
  - Atomic update for immutability (CHECK constraint enforced)

**Query Methods**
- `list_by_session(session_id, page, page_size)` → QuerySet[Report]
  - Order by generated_at DESC
- `list_by_user(user_id, page, page_size)` → QuerySet[Report]
  - Lecturer sees only own reports
- `list_by_date_range(from_date, to_date, page, page_size)` → QuerySet[Report]
- `list_exported(page, page_size)` → QuerySet[Report]
  - Filter: file_path IS NOT NULL

**Authorization Helpers**
- `can_access_report(report_id, user_id, user_role)` → bool
  - Lecturer: only if session.lecturer_id == user_id
  - Admin: always True

**Cross-Context Aggregation** (used by ReportService)
- `get_session_details(session_id)` → dict
  - Fetches: course, program, stream, lecturer, time_created, time_ended, location
  - Cross-context: Session Management
- `get_eligible_students(session_id)` → list[StudentProfile]
  - Logic: Fetch session.program_id and session.stream_id
  - If stream_id is NULL: all students in program
  - If stream_id is set: students in that stream
  - Cross-context: Academic Structure, User Management
- `get_attendance_for_session(session_id)` → list[Attendance]
  - Cross-context: Attendance Recording
- `calculate_statistics(session_id)` → dict
  - Returns: { total_eligible, present, late, absent, present_percent, late_percent, absent_percent }
  - Uses AttendanceAggregator logic:
    - Present: status="present" AND is_within_radius=True
    - Late: status="late" OR is_within_radius=False
    - Absent: No attendance record

**Indexes**
- INDEX: session_id
- INDEX: generated_by_id
- INDEX: generated_at
- INDEX: (file_path, file_type) - for exported reports query

**Priority**: HIGH (performance critical for aggregation queries)

**Reference**: [`docs/contexts/reporting/repositories_guide.md`](docs/contexts/reporting/repositories_guide.md)

---

## Cross-Context Repository Patterns

### Foreign Key Validation

When creating records with cross-context foreign keys, repositories should validate existence:

```python
# Example: SessionRepository creating a session
def create(self, program_id, course_id, lecturer_id, ...):
    # Validate foreign keys exist (cross-context)
    if not ProgramRepository.exists_by_id(program_id):
        raise ProgramNotFoundError(program_id)
    if not CourseRepository.exists_by_id(course_id):
        raise CourseNotFoundError(course_id)
    if not LecturerProfileRepository.exists_by_id(lecturer_id):
        raise LecturerNotFoundError(lecturer_id)
    
    # Create session
    session = Session.objects.create(...)
    return session
```

### Data Aggregation Strategies

**Strategy 1: Repository Method** (Preferred for simple queries)
```python
# ReportRepository fetches attendance data
def get_attendance_for_session(self, session_id):
    return AttendanceRepository.list_by_session(session_id)
```

**Strategy 2: Service Orchestration** (Preferred for complex logic)
```python
# ReportService orchestrates multiple repositories
def generate_report(self, session_id):
    session = SessionRepository.get_by_id(session_id)
    eligible = self._get_eligible_students(session)
    attendance = AttendanceRepository.list_by_session(session_id)
    aggregated = AttendanceAggregator.aggregate(eligible, attendance)
    report = ReportRepository.create(session_id, aggregated)
    return report
```

**Strategy 3: API Call** (When direct DB access violates boundaries)
```python
# Reporting calls Academic Structure API
def get_eligible_students(self, session_id):
    response = requests.get(f"/api/academic-structure/students/?session={session_id}")
    return response.json()
```

---

## Query Optimization Strategies

### 1. Eager Loading (N+1 Prevention)

**Problem**: Fetching related objects in a loop causes N+1 queries
```python
# BAD: N+1 queries
sessions = Session.objects.all()
for session in sessions:
    print(session.course.name)  # 1 query per session
```

**Solution**: Use select_related for ForeignKey
```python
# GOOD: 1 query with JOIN
sessions = Session.objects.select_related('course', 'lecturer', 'program').all()
for session in sessions:
    print(session.course.name)  # No additional query
```

**Priority**: CRITICAL (performance)

---

### 2. Bulk Operations

**Problem**: Creating many records one-by-one
```python
# BAD: N queries
for student in students:
    EmailNotification.objects.create(session_id=session.id, student_profile_id=student.id, ...)
```

**Solution**: Use bulk_create
```python
# GOOD: 1 query
notifications = [
    EmailNotification(session_id=session.id, student_profile_id=student.id, ...)
    for student in students
]
EmailNotification.objects.bulk_create(notifications, batch_size=100)
```

**Priority**: HIGH (especially for Email Notifications)

---

### 3. Indexes for Common Queries

**Rule**: Index fields used in WHERE, JOIN, ORDER BY

```python
# Frequent query: list sessions by lecturer, ordered by time
sessions = Session.objects.filter(lecturer_id=lecturer_id).order_by('-time_created')

# Required indexes:
# - INDEX on lecturer_id (for WHERE)
# - INDEX on time_created (for ORDER BY)
```

**Priority**: HIGH

---

### 4. Pagination for Large Datasets

**Always paginate** list queries to avoid loading all records

```python
# Repository method signature
def list_by_program(self, program_id, page=1, page_size=20):
    offset = (page - 1) * page_size
    return Student.objects.filter(program_id=program_id).offset(offset).limit(page_size)
```

**Priority**: HIGH

---

### 5. Aggregation in Database

**Problem**: Fetching all records and counting in Python
```python
# BAD: Fetch all attendance records
attendances = Attendance.objects.filter(session_id=session_id)
present = sum(1 for a in attendances if a.status == 'present')
```

**Solution**: Use database aggregation
```python
# GOOD: Count in DB
from django.db.models import Count, Q
stats = Attendance.objects.filter(session_id=session_id).aggregate(
    present=Count('id', filter=Q(status='present', is_within_radius=True)),
    late=Count('id', filter=Q(status='late') | Q(is_within_radius=False))
)
```

**Priority**: CRITICAL (Reporting context)

---

## Repository Testing Strategy

### Unit Tests (Repository Layer)

**Focus**: Test query logic, not Django ORM itself

```python
# Test: get_by_email (case-insensitive)
def test_get_by_email_case_insensitive():
    # Arrange
    user = UserRepository.create(email="Test@Example.com", ...)
    
    # Act
    found = UserRepository.get_by_email("test@example.com")
    
    # Assert
    assert found.id == user.id
```

**Priority**: HIGH

---

### Integration Tests (Cross-Context)

**Focus**: Test foreign key validations and aggregations

```python
# Test: SessionRepository validates program exists
def test_create_session_invalid_program():
    with pytest.raises(ProgramNotFoundError):
        SessionRepository.create(program_id=9999, ...)
```

**Priority**: MEDIUM

---

### Performance Tests

**Focus**: Test N+1 prevention, bulk operations

```python
# Test: Ensure select_related used
def test_list_sessions_no_n_plus_1(django_assert_num_queries):
    SessionRepository.create(...)  # Create 10 sessions
    
    with django_assert_num_queries(1):  # Expect 1 query (with JOIN)
        sessions = SessionRepository.list_by_lecturer(lecturer_id)
        for session in sessions:
            _ = session.course.name  # Should not trigger query
```

**Priority**: HIGH

---

## Error Handling Patterns

### Standard Error Mapping

```python
# Repository method
def get_by_id(self, session_id):
    try:
        return Session.objects.select_related('course', 'lecturer').get(id=session_id)
    except Session.DoesNotExist:
        raise SessionNotFoundError(f"Session {session_id} not found")
    except Exception as e:
        raise RepositoryError(f"Unexpected error: {str(e)}")
```

### Constraint Violations

```python
from django.db import IntegrityError

def create(self, email, ...):
    try:
        user = User.objects.create(email=email, ...)
        return user
    except IntegrityError as e:
        if 'unique constraint' in str(e).lower() and 'email' in str(e).lower():
            raise DuplicateEmailError(f"Email {email} already exists")
        raise RepositoryError(f"Database error: {str(e)}")
```

---

## Quick Reference: Core Repositories

| Context | Repository | Key Methods | Priority | Cross-Context Dependencies |
|---------|-----------|-------------|----------|---------------------------|
| User Management | UserRepository | get_by_email, exists_by_email | CRITICAL | None |
| User Management | StudentProfileRepository | get_by_student_id, list_by_program | CRITICAL | Academic Structure (program_id, stream_id) |
| User Management | LecturerProfileRepository | get_by_user_id, list_active_lecturers | HIGH | None |
| Academic Structure | ProgramRepository | get_by_code, can_be_deleted | HIGH | None |
| Academic Structure | StreamRepository | list_by_program, exists_by_program_and_name | MEDIUM | Program |
| Academic Structure | CourseRepository | list_by_lecturer, can_be_deleted | HIGH | Program, Lecturer, Session Management |
| Session Management | SessionRepository | exists_overlapping_for_lecturer, list_active_by_lecturer | CRITICAL | Program, Course, Lecturer, Stream |
| Attendance Recording | AttendanceRepository | exists_for_student_and_session, get_session_statistics | CRITICAL | Student, Session |
| Email Notifications | EmailNotificationRepository | bulk_create, get_by_token, list_pending | HIGH | Session, Student |
| Reporting | ReportRepository | get_session_details, get_eligible_students, calculate_statistics | HIGH | Session, Student, Attendance |

---

## Implementation Order

**Phase 1: Foundation**
1. User Management repositories (User, StudentProfile, LecturerProfile)
2. Academic Structure repositories (Program, Stream, Course)

**Phase 2: Core Workflow**
3. Session Management repository (Session)
4. Email Notifications repository (EmailNotification)

**Phase 3: User Actions**
5. Attendance Recording repository (Attendance)

**Phase 4: Analytics**
6. Reporting repository (Report)

---

## Additional Resources

For detailed implementation guides, see:
- User Management: [`docs/contexts/user-management/repositories_guide.md`](docs/contexts/user-management/repositories_guide.md)
- Academic Structure: [`docs/contexts/academic-structure/repositories_guide.md`](docs/contexts/academic-structure/repositories_guide.md)
- Session Management: [`docs/contexts/session-management/repositories_guide.md`](docs/contexts/session-management/repositories_guide.md)
- Attendance Recording: [`docs/contexts/attendance-recording/repositories_guide.md`](docs/contexts/attendance-recording/repositories_guide.md)
- Email Notifications: [`docs/contexts/email-notifications/repositories_guide.md`](docs/contexts/email-notifications/repositories_guide.md)
- Reporting: [`docs/contexts/reporting/repositories_guide.md`](docs/contexts/reporting/repositories_guide.md)

---

**Status**: ✅ Complete repository architecture documented across all bounded contexts