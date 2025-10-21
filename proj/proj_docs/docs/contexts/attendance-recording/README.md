# README.md

Brief: Overview and implementation manual for Attendance Recording context. Scope, entities, business rules, integration points.

# Attendance Recording Bounded Context

## Purpose

This bounded context handles the actual attendance marking process including QR code verification, location validation (30m radius), and attendance record creation.

## Scope

### What This Context Handles
- JWT token validation from email links
- QR code verification (student ID matching)
- GPS location validation (30m radius check)
- Attendance record creation
- Duplicate attendance prevention
- Student eligibility validation

### What This Context Does NOT Handle
- Session creation → handled by Session Management Context
- Email notification sending → handled by Email Notification Context
- Report generation → handled by Reporting Context
- User authentication → uses JWT tokens from Email Notification Context
- Student registration → handled by User Management Context

## Core Entities

### Attendance
- **Primary entity** representing a single attendance record
- Attributes:
  - `attendance_id` (Primary Key, Integer, Auto-increment) - Unique identifier
  - `student_profile_id` (Foreign Key → StudentProfile.student_profile_id, NOT NULL) - Student who marked attendance
  - `session_id` (Foreign Key → Session.session_id, NOT NULL) - Session attended
  - `time_recorded` (DateTime, NOT NULL, Auto-set) - When attendance was marked
  - `latitude` (Decimal, NOT NULL) - Student's latitude when marking attendance
  - `longitude` (Decimal, NOT NULL) - Student's longitude when marking attendance
  - `status` (String, NOT NULL) - Attendance status: `present`, `late`, etc.
  - `is_within_radius` (Boolean, NOT NULL) - Whether student was within 30m of session location

**Important Notes:**
- One attendance record per student per session (enforced by UNIQUE constraint)
- Student's location is captured and stored for audit
- `is_within_radius` is calculated and stored (not editable)
- `time_recorded` is set automatically (server timestamp, not client)
- Status can be `present` (on time) or `late` (after grace period)

## Business Rules

### Attendance Marking Workflow

When a student clicks the email link and scans QR code:

1. **JWT Token Validation**:
   - Verify token signature (not forged)
   - Check token has not expired
   - Extract `student_profile_id` and `session_id` from token

2. **QR Code Verification**:
   - Student scans their student ID QR code
   - Extract `student_id` from QR data (format: `BCS/234344`)
   - Load StudentProfile by `student_profile_id` (from token)
   - **Verify**: `scanned_student_id == student.student_id`
   - **Purpose**: Prevent students from using someone else's email link

3. **Session Validation**:
   - Session must exist
   - Current time must be within session window (`time_created` <= now <= `time_ended`)
   - Session must not have ended

4. **Student Eligibility Validation**:
   - Student's `program_id` must match session's `program_id`
   - If session has `stream_id` set, student's `stream_id` must match
   - Student account must be active (`is_active = True`)

5. **Location Validation** (30m radius):
   - Student provides current GPS coordinates (latitude, longitude)
   - Calculate distance between student location and session location
   - Use Haversine formula for accurate distance calculation
   - **Pass**: Distance <= 30 meters → `is_within_radius = True`
   - **Fail**: Distance > 30 meters → `is_within_radius = False` (attendance still recorded)

6. **Duplicate Prevention**:
   - Check if attendance already exists for this student and session
   - UNIQUE constraint prevents duplicates at database level
   - Return clear error if duplicate attempt

7. **Attendance Recording**:
   - Create Attendance record with all details
   - Set `time_recorded` to current server time
   - Set `status` based on timing (present vs late)
   - Store `is_within_radius` result
   - Return success response

### Attendance Status Determination

- **present**: Marked within session time window AND within 30m radius
- **late**: Marked within session time window BUT outside 30m radius OR near end of window
- **absent**: No attendance record exists (determined during reporting)

**Important Notes:**
- Status is determined by system, not by student
- Even if outside 30m, attendance is recorded (for audit)
- `is_within_radius = False` is a flag, not a blocker (lecturer can review)

### Distance Calculation (Haversine Formula)

```python
from math import radians, cos, sin, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two GPS coordinates in meters
    """
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Earth radius in meters
    r = 6371000
    
    return c * r
```

## Validation Rules

### JWT Token Validation
- Must be valid JWT (signature check)
- Must not be expired (`exp` claim)
- Must contain `student_profile_id` and `session_id`
- Token format must be correct

### QR Code Validation
- Must match format: `^[A-Z]{3}/[0-9]{6}$` (e.g., `BCS/234344`)
- Scanned student_id must match StudentProfile.student_id from token
- **Anti-fraud check**: Prevents email forwarding

### GPS Coordinates Validation
- Latitude: -90 to 90 degrees
- Longitude: -180 to 180 degrees
- Must be decimal values
- Cannot be (0, 0) (default/invalid coordinates)

### Session Time Window
- Current time >= `session.time_created`
- Current time <= `session.time_ended`
- Session must not have ended

### Student Eligibility
- Student program matches session program
- If session has stream, student stream must match
- Student account is active

## Database Constraints

### Attendance Table
```sql
CREATE TABLE attendance (
  attendance_id SERIAL PRIMARY KEY,
  student_profile_id INTEGER NOT NULL REFERENCES student_profiles(student_profile_id) ON DELETE CASCADE,
  session_id INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  time_recorded TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  latitude DECIMAL(10, 8) NOT NULL CHECK (latitude BETWEEN -90 AND 90),
  longitude DECIMAL(11, 8) NOT NULL CHECK (longitude BETWEEN -180 AND 180),
  status VARCHAR(20) NOT NULL,
  is_within_radius BOOLEAN NOT NULL,
  
  CONSTRAINT unique_attendance_per_student_session UNIQUE(student_profile_id, session_id)
);

CREATE INDEX idx_attendance_student_id ON attendance(student_profile_id);
CREATE INDEX idx_attendance_session_id ON attendance(session_id);
CREATE INDEX idx_attendance_time_recorded ON attendance(time_recorded);
CREATE INDEX idx_attendance_status ON attendance(status);
```

**Important Constraint Notes:**
- `UNIQUE(student_profile_id, session_id)`: One attendance per student per session
- `ON DELETE CASCADE`: Deleting student or session deletes attendance records
- CHECK constraints on GPS coordinates
- Indexes for efficient querying (by session, by student, by time)

## Django Implementation Structure

```
attendance_recording/
├── models.py           # Attendance model
├── repositories.py     # AttendanceRepository
├── services.py         # AttendanceService, LocationValidator, QRCodeValidator
├── handlers.py         # MarkAttendanceHandler
├── views.py           # API endpoints
├── serializers.py     # Request/response serialization
├── validators.py      # Token, QR, GPS, session validation
├── permissions.py     # Custom permission (token-based)
├── urls.py            # URL routing
├── tests/             # Unit and integration tests
└── migrations/        # Database migrations
```

## Integration Points

### Outbound Dependencies (What We Call)
- **Email Notification Context**: 
  - Validate JWT token (decode and verify)
  - Get EmailNotification record to ensure token is valid
  
- **Session Management Context**: 
  - Get session details (location, time window, program, stream)
  - Check if session is active
  
- **User Management Context**: 
  - Get StudentProfile details (student_id, program_id, stream_id)
  - Verify student is active
  
- **Infrastructure**: 
  - JWT library for token decoding
  - Haversine distance calculation

### Inbound Dependencies (Who Calls Us)
- **Reporting Context**: 
  - Query attendance records for report generation
  - Get attendance status by session

## Three-Factor Verification

The system uses three layers of security:

1. **JWT Token** (What you received in email):
   - Contains `student_profile_id` and `session_id`
   - Time-limited (expires after 30-60 minutes)
   - Cannot be forged (signed with secret key)

2. **QR Code** (What you have - physical ID card):
   - Contains institutional `student_id` (e.g., `BCS/234344`)
   - Must match the student linked to the token
   - Prevents email forwarding fraud

3. **GPS Location** (Where you are - physical presence):
   - Must be within 30 meters of session location
   - Prevents remote attendance marking
   - Verifies physical presence at the venue

**All three must pass for successful attendance marking.**

## Error Handling

### Token Errors
- **Invalid token**: Token signature verification failed
- **Expired token**: Token has passed expiry time
- **Missing claims**: Token doesn't contain required fields

### QR Code Errors
- **Invalid format**: QR doesn't match student ID pattern
- **Mismatch**: Scanned student_id doesn't match token student
- **Fraud attempt**: Using someone else's email link

### Session Errors
- **Session not found**: Invalid session_id
- **Session ended**: Current time past session end time
- **Session not started**: Current time before session start time

### Eligibility Errors
- **Program mismatch**: Student not in session's target program
- **Stream mismatch**: Student not in session's target stream
- **Inactive student**: Student account deactivated

### Location Errors
- **Invalid coordinates**: GPS values out of range
- **Outside radius**: Student more than 30m from session location (warning, not blocker)

### Duplicate Errors
- **Already marked**: Attendance already exists for this student and session
- **HTTP 409 Conflict** returned

## Files in This Context

### 1. `README.md` (this file)
Overview of the bounded context

### 2. `models_guide.md`
Step-by-step guide for creating Django models:
- Attendance model
- UNIQUE constraint
- GPS coordinate fields
- Status field

### 3. `repositories_guide.md`
Guide for creating repository layer:
- AttendanceRepository
- Check if attendance exists (duplicate prevention)
- Query by session, by student
- Complex queries for reports

### 4. `services_guide.md`
Guide for creating domain services:
- AttendanceService (orchestrate validation + recording)
- LocationValidator (Haversine distance calculation)
- QRCodeValidator (format and match validation)
- JWTTokenValidator (decode and verify)
- SessionValidator (time window, eligibility)

### 5. `handlers_guide.md`
Guide for creating application layer handlers:
- MarkAttendanceHandler
  - Validate token
  - Verify QR code
  - Check session status
  - Validate eligibility
  - Calculate distance
  - Prevent duplicates
  - Create attendance record

### 6. `views_guide.md`
Guide for creating API endpoints:
- POST /api/v1/attendance/mark/
  - Public endpoint (uses token auth)
  - Request: {token, scanned_student_id, latitude, longitude}
  - Response: Success or detailed error

### 7. `testing_guide.md`
Guide for writing tests:
- Test full attendance marking flow
- Test token validation (valid, expired, invalid)
- Test QR mismatch (fraud attempt)
- Test location validation (within/outside 30m)
- Test duplicate prevention
- Test session time window validation
- Test student eligibility validation

## Implementation Order

1. **Models** (`models_guide.md`) - Attendance model
2. **Repositories** (`repositories_guide.md`) - Data access + duplicate check
3. **Services** (`services_guide.md`) - Validators (JWT, QR, Location, Session)
4. **Handlers** (`handlers_guide.md`) - MarkAttendanceHandler (orchestration)
5. **Views** (`views_guide.md`) - Public API endpoint
6. **Tests** (`testing_guide.md`) - Comprehensive testing

## Next Steps

After reading this overview:
1. Understand three-factor verification (Token + QR + GPS)
2. Review Haversine distance calculation
3. Verify QR code anti-fraud mechanism
4. Understand duplicate prevention
5. Review all validation rules
6. Understand error handling strategies
7. Proceed to detailed guide files

---

**Status**: 📝 Overview Complete - Ready for detailed guide creation
