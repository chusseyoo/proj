# README.md

Brief: Overview and implementation manual for Session Management context. Scope, entities, business rules, integration points.

# Session Management Bounded Context

## Purpose

This bounded context handles the creation and lifecycle management of attendance sessions. Sessions are created by lecturers to enable students to mark their attendance for specific courses.

## Scope

### What This Context Handles
- Session creation by lecturers
- Session configuration (course, program, stream, time, location)
- Session lifecycle (created, active, ended)
- Session validation and authorization
- Capture lecturer's GPS location

### What This Context Does NOT Handle
- Email notification sending → handled by Email Notification Context
- Attendance marking → handled by Attendance Recording Context
- Report generation → handled by Reporting Context
- User authentication → handled by User Management Context
- Course/program management → handled by Academic Structure Context

## Core Entities

### Session
- **Primary entity** representing an attendance session created by a lecturer
- Attributes:
  - `session_id` (Primary Key, Integer, Auto-increment) - Unique identifier
  - `program_id` (Foreign Key → Program.program_id, NOT NULL) - Target program
  - `course_id` (Foreign Key → Course.course_id, NOT NULL) - Course session is for
  - `lecturer_id` (Foreign Key → LecturerProfile.lecturer_id, NOT NULL) - Session creator
  - `stream_id` (Foreign Key → Stream.stream_id, **NULLABLE**) - Optional target stream
    - **NULL**: Session targets entire program
    - **NOT NULL**: Session targets specific stream only
  - `date_created` (Date, NOT NULL) - Date when session was created
  - `time_created` (DateTime, NOT NULL) - Session start time
  - `time_ended` (DateTime, NOT NULL) - Session end time
  - `latitude` (Decimal, NOT NULL) - Lecturer's latitude coordinate when creating session
  - `longitude` (Decimal, NOT NULL) - Lecturer's longitude coordinate when creating session

**Important Notes:**
- Session creation triggers email notification generation (handled by Email Notification Context)
- `stream_id` nullable: if NULL, all students in program are eligible; if set, only students in that stream
- Lecturer's location is captured at session creation time
- Students must be within 30m of this location to mark attendance
- Session has a time window (`time_created` to `time_ended`)
- Only the assigned lecturer for the course can create sessions

## Business Rules

### Session Creation

1. **Authorization**:
   - Only lecturers can create sessions
   - Lecturer must be assigned to the course (`Course.lecturer_id = lecturer_id`)
   - Lecturer account must be active (`is_active = True`)

2. **Course Validation**:
   - Course must exist and be active
   - Course must have an assigned lecturer
   - Course must belong to the specified program

3. **Program/Stream Targeting**:
   - Must specify a `program_id` (required)
   - `stream_id` is optional:
     - If program has `has_streams = False`: `stream_id` must be NULL
     - If program has `has_streams = True`: can be NULL (entire program) or specify a stream
   - If `stream_id` is provided, stream must belong to the specified program

4. **Time Validation**:
   - `time_ended` must be after `time_created`
   - Typical session duration: 30 minutes to 3 hours
   - Sessions in the past are allowed (retroactive sessions)
   - Cannot create overlapping sessions (same course, same time window)

5. **Location Capture**:
   - Lecturer's GPS coordinates are captured at session creation
   - Latitude: -90 to 90 degrees
   - Longitude: -180 to 180 degrees
   - Coordinates are used for 30m radius validation during attendance

### Session Lifecycle

1. **Created**: Session is created and email notifications are queued
2. **Active**: Current time is between `time_created` and `time_ended`
3. **Ended**: Current time is after `time_ended`

**Important Notes:**
- Sessions don't have explicit "active" status in database
- Active/ended status is derived from current time vs `time_created`/`time_ended`
- Students can only mark attendance during active window
- Email notifications are sent immediately upon creation

### Eligible Students

Students eligible for a session are determined by:
- `program_id` matches student's program
- If `stream_id` is NULL: all students in program
- If `stream_id` is set: only students in that stream
- Student account must be active (`is_active = True`)

## Validation Rules

### Time Window Validation
- `time_created` < `time_ended`
- Duration between 10 minutes and 24 hours
- Both must be valid timestamps

### Location Validation
- Latitude: must be between -90 and 90
- Longitude: must be between -180 and 180
- Both must be decimal values with up to 8 decimal places

### Program/Stream Consistency
- If `stream_id` provided, must belong to `program_id`
- If program `has_streams = False`, `stream_id` must be NULL
- If program `has_streams = True`, `stream_id` can be NULL or valid stream

### Course Authorization
- Lecturer creating session must match `Course.lecturer_id`
- Course must belong to specified program

## Database Constraints

### Session Table
```sql
CREATE TABLE sessions (
  session_id SERIAL PRIMARY KEY,
  program_id INTEGER NOT NULL REFERENCES programs(program_id),
  course_id INTEGER NOT NULL REFERENCES courses(course_id),
  lecturer_id INTEGER NOT NULL REFERENCES lecturer_profiles(lecturer_id),
  stream_id INTEGER REFERENCES streams(stream_id),  -- NULLABLE
  date_created DATE NOT NULL,
  time_created TIMESTAMPTZ NOT NULL,
  time_ended TIMESTAMPTZ NOT NULL,
  latitude DECIMAL(10, 8) NOT NULL CHECK (latitude BETWEEN -90 AND 90),
  longitude DECIMAL(11, 8) NOT NULL CHECK (longitude BETWEEN -180 AND 180),
  
  CONSTRAINT valid_time_window CHECK (time_ended > time_created)
);

CREATE INDEX idx_sessions_course_id ON sessions(course_id);
CREATE INDEX idx_sessions_lecturer_id ON sessions(lecturer_id);
CREATE INDEX idx_sessions_program_stream ON sessions(program_id, stream_id);
CREATE INDEX idx_sessions_time ON sessions(time_created, time_ended);
```

**Important Constraint Notes:**
- `stream_id` is nullable (targets entire program if NULL)
- CHECK constraint ensures valid time window
- CHECK constraints ensure valid GPS coordinates
- Indexes on program/stream for efficient student eligibility queries
- Index on time for active session queries

## Django Implementation Structure

```
session_management/
├── models.py           # Session model
├── repositories.py     # SessionRepository
├── services.py         # SessionService (validation, eligibility)
├── handlers.py         # CreateSessionHandler
├── views.py           # API endpoints
├── serializers.py     # Request/response serialization
├── validators.py      # Time, location, program/stream validation
├── permissions.py     # LecturerOnly permission
├── urls.py            # URL routing
├── tests/             # Unit and integration tests
└── migrations/        # Database migrations
```

## Integration Points

### Outbound Dependencies (What We Call)
- **Academic Structure Context**: 
  - Validate `program_id`, `course_id`, `stream_id`
  - Check `Program.has_streams` flag
  - Verify course belongs to program
  - Get course lecturer
  
- **User Management Context**: 
  - Validate lecturer is authorized for course
  - Check lecturer is active
  
- **Email Notification Context**: 
  - Trigger email notification generation after session creation
  - Pass session details (session_id, eligible student criteria)

### Inbound Dependencies (Who Calls Us)
- **Attendance Recording Context**: 
  - Get session details (location, time window, program/stream)
  - Validate if session is active
  - Check student eligibility for session
  
- **Reporting Context**: 
  - Get session metadata for reports
  - List sessions by lecturer, course, or date range

## Side Effects

When a session is created, the following happens automatically:

1. **Session record saved** to database
2. **Email notifications queued** (handled by Email Notification Context):
   - System identifies eligible students (by program/stream)
   - Creates EmailNotification records with JWT tokens
   - Queues emails for asynchronous sending
3. **Success response returned** to lecturer

## Files in This Context

### 1. `README.md` (this file)
Overview of the bounded context

### 2. `models_guide.md`
Step-by-step guide for creating Django models:
- Session model
- Nullable stream_id handling
- GPS coordinate fields
- Time window validation

### 3. `repositories_guide.md`
Guide for creating repository layer:
- SessionRepository (CRUD operations)
- Query active sessions
- Query sessions by lecturer, course, date range
- Get eligible students for session

### 4. `services_guide.md`
Guide for creating domain services:
- SessionService (business logic)
- Validate session creation authorization
- Validate program/stream consistency
- Calculate eligible students
- Check session status (active/ended)

### 5. `handlers_guide.md`
Guide for creating application layer handlers:
- CreateSessionHandler
  - Validate inputs
  - Check lecturer authorization
  - Save session
  - Trigger email notification generation
  - Return response

### 6. `views_guide.md`
Guide for creating API endpoints:
- POST /api/v1/sessions/ (create session)
- GET /api/v1/sessions/ (list lecturer's sessions)
- GET /api/v1/sessions/{id}/ (get session details)
- GET /api/v1/sessions/{id}/status/ (check if active)

### 7. `permissions_guide.md`
Guide for implementing access control:
- IsLecturer permission
- IsSessionOwner permission (lecturer can only view own sessions)

### 8. `testing_guide.md`
Guide for writing tests:
- Test session creation with/without streams
- Test authorization (only assigned lecturer can create)
- Test time window validation
- Test GPS coordinate validation
- Test program/stream consistency
- Test email notification triggering (mock)

## Implementation Order

1. **Models** (`models_guide.md`) - Session model with constraints
2. **Repositories** (`repositories_guide.md`) - Data access
3. **Services** (`services_guide.md`) - Business logic and validation
4. **Handlers** (`handlers_guide.md`) - Orchestration + email trigger
5. **Serializers & Validators** (part of `views_guide.md`)
6. **Views** (`views_guide.md`) - Lecturer API endpoints
7. **Permissions** (`permissions_guide.md`) - Lecturer authorization
8. **Tests** (`testing_guide.md`) - Comprehensive testing

## Next Steps

After reading this overview:
1. Understand session targeting (program vs stream)
2. Verify GPS location capture and validation
3. Confirm time window constraints
4. Understand lecturer authorization rules
5. Review integration with Email Notification Context
6. Proceed to detailed guide files

---

**Status**: 📝 Overview Complete - Ready for detailed guide creation
