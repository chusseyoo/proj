# repositories_guide.md

Brief: Complete repository layer specification for Attendance Recording. Encapsulates data access with focus on duplicate detection, session/student queries, and efficient reporting queries. Critical for preventing duplicate submissions and generating attendance reports.

---

## Repository Purpose

**Why Repositories Matter in Attendance Recording**:
- **Duplicate prevention**: Fast existence checks before creating records
- **Reporting**: Efficient queries for attendance lists and statistics
- **Data integrity**: Centralize database operations to enforce constraints
- **Performance**: Optimize queries with proper indexing and select_related

**Priority: CRITICAL** - Core data access layer for immutable attendance records

---

# ATTENDANCEREPOSITORY

## Overview

**File Location**: `repositories/attendance_repository.py`

**Responsibilities**:
- CRUD operations for Attendance records
- Duplicate detection (exists checks)
- Session-based queries (attendance lists)
- Student-based queries (attendance history)
- Status filtering (present/late/absent)
- Reporting statistics

**Dependencies**:
- Attendance model
- Django ORM QuerySet API

**Why Separate File**: 
- Keeps `models.py` focused on model definitions
- Single source of truth for all data access patterns
- Easy to mock in service tests

---

## Method Categories

### Category 1: CRUD Operations
**Priority: CRITICAL** - Basic data access

#### create(data: dict) → Attendance
- **Purpose**: Create single attendance record
- **Input**: Dictionary with keys:
  ```python
  {
    "student_profile_id": int,
    "session_id": int,
    "latitude": Decimal,
    "longitude": Decimal,
    "status": str,  # "present" or "late"
    "is_within_radius": bool
  }
  ```
- **Note**: `time_recorded` set automatically by model (auto_now_add=True)
- **Returns**: Saved Attendance instance
- **Error Handling**:
  - Duplicate (unique constraint) → IntegrityError
  - Invalid FK → ForeignKey.DoesNotExist
- **Why Important**: Single entry point for creating attendance
- **Immutability**: Once created, record cannot be modified (no update method)

#### get_by_id(attendance_id: int) → Attendance
- **Purpose**: Retrieve attendance record by primary key
- **Returns**: Attendance instance
- **Raises**: Attendance.DoesNotExist if not found
- **Use Case**: Admin viewing specific attendance details, dispute resolution
- **Optimization**: Use `select_related('student_profile__user', 'session')` for related data

#### delete(attendance_id: int) → None
- **Purpose**: Hard delete attendance record
- **Use Case**: Lecturer removes mistaken attendance (rare)
- **Why Limited Use**: Attendance is immutable; deletion is exceptional
- **Authorization**: Must verify lecturer owns the session before delete

**Important**: No update method! Attendance records are immutable once created.

---

### Category 2: Duplicate Detection
**Priority: CRITICAL** - Prevent fraud and data integrity

#### exists_for_student_and_session(student_profile_id: int, session_id: int) → bool
- **Purpose**: Check if attendance already exists
- **Query**: `SELECT COUNT(*) WHERE student_profile_id=? AND session_id=?`
- **Returns**: True if exists, False otherwise
- **Performance**: Fast (indexed on both fields via unique constraint)
- **Why Critical**: 
  - Pre-check before creating record (better UX than database error)
  - Prevents duplicate attendance submissions
  - Returns clear error message to student

**Usage Pattern**:
```python
if repository.exists_for_student_and_session(student_id, session_id):
    raise DuplicateAttendanceError("You have already marked attendance for this session")
else:
    repository.create({...})
```

#### get_by_student_and_session(student_profile_id: int, session_id: int) → Attendance | None
- **Purpose**: Retrieve existing attendance (if any)
- **Returns**: Attendance instance or None
- **Use Case**: 
  - Show student their recorded attendance details
  - Verify what time they marked attendance
  - Check their location and status

---

### Category 3: Session-Based Queries
**Priority: HIGH** - Reporting and attendance lists

#### get_by_session(session_id: int) → QuerySet[Attendance]
- **Purpose**: Get all attendance records for a session
- **Query**: `WHERE session_id = ?`
- **Ordering**: `time_recorded ASC` (chronological order)
- **Optimization**: `select_related('student_profile__user')` to get student names
- **Use Case**:
  - Lecturer views attendance list for session
  - Generate attendance report
  - Count present/late students

#### get_by_session_with_status(session_id: int, status: str) → QuerySet[Attendance]
- **Purpose**: Filter session attendance by status
- **Query**: `WHERE session_id = ? AND status = ?`
- **Status Options**: "present", "late"
- **Use Case**:
  - "Show me only late students for this session"
  - Count present students
- **Optimization**: Index on (session_id, status)

#### count_by_session(session_id: int) → dict
- **Purpose**: Get attendance statistics for session
- **Returns**:
  ```python
  {
    "total": 45,
    "present": 40,
    "late": 5,
    "absent": 5  # calculated: eligible students - total
  }
  ```
- **Why Useful**: Quick stats for dashboards and reports
- **Note**: Absent count requires cross-context query (eligible students from Session Management)

#### get_students_outside_radius(session_id: int) → QuerySet[Attendance]
- **Purpose**: Find students who marked attendance outside 30m radius
- **Query**: `WHERE session_id = ? AND is_within_radius = FALSE`
- **Use Case**:
  - Lecturer reviews potential fraud cases
  - Identify GPS spoofing attempts
  - Excuse legitimate cases (building structure, GPS inaccuracy)
- **Why Important**: Audit trail for location violations

---

### Category 4: Student-Based Queries
**Priority: HIGH** - Student history and patterns

#### get_by_student(student_profile_id: int, limit: int = None) → QuerySet[Attendance]
- **Purpose**: Get student's attendance history
- **Query**: `WHERE student_profile_id = ?`
- **Ordering**: `time_recorded DESC` (most recent first)
- **Optional Limit**: For pagination or "recent 10 sessions"
- **Optimization**: `select_related('session__course')` to get course names
- **Use Case**:
  - Student views their attendance history
  - Calculate attendance percentage
  - Generate student transcript

#### count_by_student(student_profile_id: int) → dict
- **Purpose**: Get student's attendance statistics
- **Returns**:
  ```python
  {
    "total_attended": 42,
    "present": 40,
    "late": 2,
    "attendance_rate": 0.933  # total_attended / total_sessions_eligible
  }
  ```
- **Why Useful**: Student performance tracking, eligibility for exams

#### get_by_student_and_course(student_profile_id: int, course_id: int) → QuerySet[Attendance]
- **Purpose**: Get student's attendance for a specific course
- **Query**: Join with Session table to filter by course
- **Use Case**: 
  - "Show my attendance for CS201"
  - Course-specific attendance percentage
- **Optimization**: `select_related('session')` then filter by course

---

### Category 5: Time-Based Queries
**Priority: MEDIUM** - Temporal analysis

#### get_by_date_range(start_date: date, end_date: date) → QuerySet[Attendance]
- **Purpose**: Get all attendance within date range
- **Query**: `WHERE DATE(time_recorded) BETWEEN ? AND ?`
- **Use Case**:
  - "All attendance this week"
  - Monthly reports
  - Semester statistics

#### get_recent_attendance(hours: int = 24) → QuerySet[Attendance]
- **Purpose**: Get recently recorded attendance
- **Query**: `WHERE time_recorded >= NOW() - INTERVAL ? HOURS`
- **Use Case**:
  - Real-time dashboard (recent activity)
  - Today's attendance count
- **Default**: Last 24 hours

---

### Category 6: Reporting and Analytics
**Priority: MEDIUM** - Aggregate statistics

#### get_attendance_summary_by_session(session_id: int) → dict
- **Purpose**: Complete session attendance breakdown
- **Returns**:
  ```python
  {
    "session_id": 123,
    "total_marked": 45,
    "present": 40,
    "late": 5,
    "within_radius": 43,
    "outside_radius": 2,
    "average_marking_time": "08:15:00",  # average time students marked
    "earliest": "08:02:00",
    "latest": "09:45:00"
  }
  ```
- **Why Useful**: Comprehensive session report for lecturers

#### get_attendance_trends(student_profile_id: int, weeks: int = 4) → dict
- **Purpose**: Analyze student's attendance patterns
- **Returns**:
  ```python
  {
    "weeks_analyzed": 4,
    "average_attendance_per_week": 3.5,
    "late_count": 2,
    "improving": True,  # trend analysis
    "at_risk": False  # low attendance flag
  }
  ```
- **Use Case**: Early intervention for struggling students

---

## Query Optimization Strategies

**Priority: HIGH** - Performance critical for reporting

### 1. Select Related for Foreign Keys
**Why**: Avoid N+1 query problem

```python
# Bad: 46 queries (1 for attendance + 45 for students)
attendance = Attendance.objects.filter(session_id=123)
for record in attendance:
    print(record.student_profile.user.email)  # Each iteration hits DB

# Good: 2 queries (1 for attendance + 1 for related data)
attendance = Attendance.objects.filter(session_id=123)\
    .select_related('student_profile__user', 'session__course')
for record in attendance:
    print(record.student_profile.user.email)  # No DB hit
```

### 2. Indexes Are Critical
**Ensure these indexes exist** (defined in model):
- `student_profile_id` (student history queries)
- `session_id` (session attendance lists)
- `time_recorded` (temporal queries)
- `status` (status filtering)
- `(student_profile_id, session_id)` (unique constraint doubles as index)

### 3. Aggregate Queries
**Use Django ORM aggregation** for counts and stats:
```python
from django.db.models import Count, Avg

# Count by status in single query
Attendance.objects.filter(session_id=123)\
    .values('status')\
    .annotate(count=Count('status'))
```

### 4. Prefetch for Many-to-Many
Not applicable here (no M2M relationships), but good pattern to know.

---

## Error Handling and Mapping

**Priority: HIGH** - Consistent error responses

### Repository-Level Errors
- **DoesNotExist**: Record not found → Service maps to `AttendanceNotFoundError`
- **IntegrityError** (unique constraint): Duplicate attendance → Service maps to `DuplicateAttendanceError`
- **ValidationError**: Field validation failed → Service maps to `InvalidAttendanceDataError`

### Service-Level Mapping Example
```python
Repository raises IntegrityError (duplicate)
    ↓
Service catches and raises DuplicateAttendanceError
    ↓
Handler catches and returns 409 Conflict
    ↓
API returns: {"error": {"code": "DuplicateAttendanceError", "message": "..."}}
```

**Why Separate**: Services own business semantics; repositories stay generic

---

## File Organization

**Priority: MEDIUM** - Maintainability

```
attendance_recording/
├── models.py                           # Attendance model
├── repositories/
│   ├── __init__.py
│   └── attendance_repository.py        # AttendanceRepository class
├── services/
│   ├── __init__.py
│   ├── attendance_service.py           # Orchestration
│   ├── location_validator.py           # Haversine distance
│   ├── qr_validator.py                 # QR code verification
│   └── token_validator.py              # JWT validation
├── tests/
│   ├── test_models.py
│   ├── test_repositories.py            # Repository tests here
│   ├── test_services.py
│   └── fixtures.py                     # Test data helpers
```

**Why Separate Folder**:
- Clear separation: `repositories/` vs `services/`
- Easy to locate data access logic
- Can add more repositories if context grows (e.g., AttendanceLog for audit)

---

## Testing Repositories

**Priority: HIGH** - Ensure data access reliability

### Test Categories
1. **CRUD tests**: Create, get, delete work correctly
2. **Duplicate detection**: exists_for_student_and_session works
3. **Query tests**: Session and student queries return correct results
4. **Constraint tests**: Unique constraint enforced at DB level
5. **Ordering tests**: Results ordered as specified

### Example Test Structure
```
tests/test_repositories.py
- test_create_attendance_success
- test_create_duplicate_raises_integrity_error
- test_exists_for_student_and_session_returns_true
- test_exists_returns_false_when_no_record
- test_get_by_session_returns_all_attendance
- test_get_by_session_ordered_by_time
- test_get_by_student_returns_history
- test_get_students_outside_radius
- test_count_by_session_includes_present_late
```

---

## Method Summary

**CRUD**:
- `create` - Create attendance record
- `get_by_id` - Retrieve by primary key
- `delete` - Remove record (rare)

**Duplicate Detection** (Critical):
- `exists_for_student_and_session` - Check if already marked
- `get_by_student_and_session` - Retrieve existing record

**Session Queries**:
- `get_by_session` - All attendance for session
- `get_by_session_with_status` - Filter by status
- `count_by_session` - Session statistics
- `get_students_outside_radius` - Location violations

**Student Queries**:
- `get_by_student` - Student attendance history
- `count_by_student` - Student statistics
- `get_by_student_and_course` - Course-specific history

**Time-Based**:
- `get_by_date_range` - Temporal filtering
- `get_recent_attendance` - Recent activity

**Reporting**:
- `get_attendance_summary_by_session` - Complete session breakdown
- `get_attendance_trends` - Student pattern analysis

---

**Status**: 📋 Complete repository specification ready for implementation

**Key Takeaways**:
1. **Duplicate detection is critical** (exists check before create)
2. **No update method** (immutable records)
3. **Select_related for efficiency** (avoid N+1 queries)
4. **Indexes on session, student, time** (reporting performance)
5. **Separate error handling** (repository errors → service exceptions)