# models_guide.md

Brief: Complete specification for Attendance model. Defines attendance records with three-factor verification (JWT token, QR code, GPS location), unique constraint per student/session, and immutable audit trail. Focus on data integrity and fraud prevention.

---

## Important Terminology

⚠️ **Student Identifier Clarification**

This document uses precise terminology for student identifiers. Understanding the distinction is critical:

| Term | Type | Example | Description |
|------|------|---------|-------------|
| **`student_profile`** | Django ForeignKey field | `attendance.student_profile` | Relationship field name in Django model. Use for ORM traversal. |
| **`student_profile_id`** | Integer (Primary Key) | `123` | Database column storing the foreign key. Auto-populated by Django. Used in queries and indexes. |
| **`student_id`** | String (Institutional ID) | `"BCS/234344"` | Human-readable identifier. Format: `^[A-Z]{3}/[0-9]{6}$`. Stored in QR codes and displayed to users. |

**Throughout This Guide:**
- **Foreign key field** is referred to as `student_profile` (the Django relationship)
- **Database column** is `student_profile_id` (the integer foreign key)
- **QR codes contain** `student_id` (the institutional string identifier)

**Usage Examples:**
```python
# Django ORM - Traverse relationship
attendance.student_profile.student_id  # Returns "BCS/234344"

# Database query - Use integer FK
Attendance.objects.filter(student_profile_id=123)

# QR code validation - Compare strings
if scanned_qr == student.student_id:  # "BCS/234344" == "BCS/234344"
```

**Why Three Identifiers?**
- `student_profile_id`: Database efficiency (integer foreign keys are faster)
- `student_id`: Human usability (printed on ID cards, readable in reports)
- `student_profile`: Developer convenience (Django relationship traversal)

---

## Model Overview

**Purpose**: Record verified student attendance for sessions with complete audit trail including location proof and timing.

**Why It Matters**: 
- **Legal/Academic**: Immutable proof of attendance for institutional records
- **Anti-fraud**: Three-factor verification prevents impersonation and remote marking
- **Analytics**: Time and location data enable attendance pattern analysis
- **Compliance**: Audit trail for academic integrity investigations

---

# ATTENDANCE MODEL

## Field Specifications

### Primary Key
- **attendance_id**: Integer, auto-increment
  - Purpose: Unique identifier for each attendance record
  - Why: Simple sequential ID for audit logs and references

**Priority: LOW** - Auto-generated, not user-facing

### Foreign Keys (Cross-Context References)

**Priority: CRITICAL** - Link attendance to students and sessions

- **student_profile**: ForeignKey → StudentProfile (User Management Context)
  - Relationship: Many attendance records per student
  - On delete: **CASCADE** (delete attendance if student removed)
  - Why CASCADE: GDPR compliance, student withdrawal
  - Nullable: **No** (every record must have a student)
  - Access pattern: `student.attendance_records.all()` → student's attendance history
  - **Important**: Links to StudentProfile, not User (keeps contexts separate)

- **session**: ForeignKey → Session (Session Management Context)
  - Relationship: Many attendance records per session
  - On delete: **CASCADE** (delete attendance if session deleted)
  - Why CASCADE: Session deletion means attendance records become meaningless
  - Nullable: **No** (every record must reference a session)
  - Access pattern: `session.attendance_records.all()` → all students who attended

### Timing Fields

**Priority: HIGH** - Immutable timestamp for audit trail

- **time_recorded**: DateTimeField with timezone, auto_now_add=True
  - Purpose: Server-side timestamp when attendance was marked
  - Why server-side: Cannot be tampered with by client
  - Why auto_now_add: Set once at creation, never modified
  - Immutable: Cannot be changed after record created
  - Use case: 
    - Determine if student was late
    - Audit trail for disputes
    - Detect patterns (always late, always on time)
  - Nullable: **No**
  - Index: **Yes** (queries by time range)

**Important**: Do NOT accept `time_recorded` from client request. Always use server time to prevent fraud.

### Location Fields (GPS Verification)

**Priority: CRITICAL** - Physical presence proof

- **latitude**: DecimalField(10, 8) 
  - Purpose: Student's latitude when marking attendance
  - Range: -90 to 90 degrees
  - Precision: 8 decimal places (~1mm accuracy)
  - Why stored: Audit trail, dispute resolution, fraud detection
  - Nullable: **No** (required for verification)
  - Example: `-1.28333412` (Nairobi, Kenya)

- **longitude**: DecimalField(11, 8)
  - Purpose: Student's longitude when marking attendance
  - Range: -180 to 180 degrees
  - Precision: 8 decimal places (~1mm accuracy)
  - Nullable: **No**
  - Example: `36.81666588`

**Why GPS Coordinates Matter**:
- **Anti-fraud**: Prevent remote attendance marking
- **Audit trail**: Proof of physical presence
- **Dispute resolution**: "I was there!" can be verified
- **Pattern analysis**: Detect spoofing (same location for all students = fraud)

**Storage Note**: Store as Decimal, not Float, to avoid precision loss. Float can cause rounding errors in distance calculations.

### Status Field

**Priority: HIGH** - Attendance classification

- **status**: CharField, max_length=20
  - Purpose: Classify attendance timing and validity
  - **Choices**:
    - `present`: On time, within radius, all checks passed
    - `late`: Within time window but late OR outside radius
  - Why not `absent`: Absence = no record exists (determined during reporting)
  - Nullable: **No**
  - Default: None (must be explicitly set by service logic)
  - Index: **Yes** (filter by status for reports)

**Status Determination Logic** (enforced in service layer):
- **present**: `is_within_radius=True` AND marked within first **30 minutes** of session start
- **late**: `is_within_radius=False` OR marked after the first **30 minutes** of session start

**Why Separate Field**: Status may be reviewed/changed by lecturer (e.g., excuse late arrival)

### Verification Result Field

**Priority: HIGH** - Location validation result

- **is_within_radius**: BooleanField
  - Purpose: Store result of 30m radius check
  - Why stored: Audit trail, cannot be recalculated if session location changes
  - Calculation: Haversine distance between student and session location
  - `True`: Student within 30 meters of session location
  - `False`: Student outside 30 meters (warning flag, not blocker)
  - Nullable: **No**
  - Why not blocker: Lecturer may excuse (GPS inaccuracy, building structure, etc.)

**Important**: This field is set ONCE at creation based on distance calculation. It is immutable.

## Database Constraints

**Priority: CRITICAL** - Data integrity and fraud prevention

### Unique Constraint
```sql
UNIQUE (student_profile_id, session_id)
```

**Why Critical**:
- **Prevents duplicate attendance**: Student cannot mark twice for same session
- **Fraud prevention**: Cannot submit multiple times to game system
- **Data integrity**: One true attendance record per student per session

**Database Behavior**: Attempting duplicate INSERT raises IntegrityError

**Service Layer Handling**: Pre-check existence before attempting insert (better UX)

### Check Constraints
```sql
CHECK (latitude BETWEEN -90 AND 90)
CHECK (longitude BETWEEN -180 AND 180)
```

**Why**: Enforce GPS coordinate validity at database level (defense in depth)

### Cascade Rules
- Student deleted → **CASCADE** delete attendance (GDPR, student withdrawal)
- Session deleted → **CASCADE** delete attendance (session canceled, no meaning)

**Why CASCADE**: Attendance records have no independent meaning without student and session

## Indexes

**Priority: HIGH** - Query performance for reporting

- **Index on student_profile_id**: Fast lookup of student's attendance history
  - Query: "Show all sessions Student A attended"
  - Use case: Student transcript, attendance percentage

- **Index on session_id**: Fast lookup of session attendance list
  - Query: "Who attended Session 123?"
  - Use case: Attendance reports, present/absent lists

- **Index on time_recorded**: Time-based queries and sorting
  - Query: "All attendance marked today"
  - Use case: Daily reports, recent activity

- **Index on status**: Filter by attendance type
  - Query: "All late attendance in past month"
  - Use case: Discipline reports, patterns

**Composite Index** (optional optimization):
```sql
INDEX (session_id, status)
```
- Use case: "All present students for Session 123" (common reporting query)

## Model Methods and Properties

**Purpose**: Encapsulate business logic and derived values

### is_late() → bool
- **Returns**: True if status is 'late'
- **Use case**: Quick status check without string comparison

### is_present() → bool
- **Returns**: True if status is 'present'
- **Use case**: Count present students

### get_distance_from_session() → float
- **Purpose**: Recalculate distance using Haversine formula
- **Returns**: Distance in meters
- **Why**: Verify stored `is_within_radius` result, debugging
- **Note**: Should match original calculation (unless session location changed)

### was_on_time() → bool
- **Logic**: Compare `time_recorded` to session timing
- **Returns**: True if marked early in session window
- **Use case**: Distinguish "present" from "late but within time"

### __str__()
- **Format**: `"{student_name} - {status} - {session}"`
- **Example**: `"John Doe - present - CS201 Lecture on 2025-10-25"`
- **Why**: Human-readable representation for admin interface

## File Organization

**Priority: MEDIUM** - Maintainability

```
attendance_recording/
├── models.py                           # Attendance model
├── repositories/                       # Separate folder for data access
│   └── attendance_repository.py        # AttendanceRepository
├── services/                           # Business logic
│   ├── attendance_service.py           # Orchestration
│   ├── location_validator.py           # Haversine distance
│   ├── qr_validator.py                 # QR code verification
│   └── token_validator.py              # JWT validation
├── handlers/
│   └── mark_attendance_handler.py      # MarkAttendanceHandler
├── views.py                            # API endpoints
├── serializers.py                      # DRF serializers
├── urls.py
└── tests/
    ├── test_models.py
    ├── test_repositories.py
    ├── test_services.py
    └── fixtures.py
```

**Why This Structure**:
- **Separation of concerns**: Models ≠ logic ≠ API
- **Service folder**: Multiple validator services for single responsibility
- **Testability**: Easy to mock services and repositories
- **Scalability**: Can add more validators without cluttering single file

## Validation Rules

**Priority: HIGH** - Enforced in services, not models

### At Creation Time (Service Layer)

1. **JWT Token Validation**
   - Token signature valid
   - Token not expired
   - Contains `student_profile_id` and `session_id`

2. **QR Code Verification**
   - Format: `^[A-Z]{3}/[0-9]{6}$` (e.g., `BCS/234344`)
   - Scanned student_id matches StudentProfile.student_id from token
   - **Anti-fraud**: Prevents using someone else's email link

3. **Session Validation**
   - Session exists
   - Session is active (current time within time window)
   - Session not ended

4. **Student Eligibility**
   - Student program matches session program
   - If session has stream, student stream matches
   - Student account is active

5. **Location Validation**
   - Coordinates in valid range (latitude: -90 to 90, longitude: -180 to 180)
   - Calculate distance to session location (Haversine formula)
   - Set `is_within_radius` based on distance <= 30m

6. **Duplicate Prevention**
   - Pre-check: Query if (student, session) record exists
   - If exists → Return 409 Conflict with clear message
   - If not exists → Create record

**Why Service Layer**: Complex cross-context validation requires orchestration, not just model constraints

### Immutability Rules

**Once attendance record is created, it CANNOT be modified.**

**Why Immutable**:
- **Academic integrity**: Attendance records are legal documents
- **Audit trail**: Changes would compromise evidence
- **Fraud prevention**: Cannot alter location or time after fact

**Exception**: Lecturer may be able to DELETE record (e.g., student marked by mistake), but not edit.

## Example Data Scenarios

### Scenario 1: Successful Attendance (On Time, Within Radius)
```
Attendance:
- student_profile_id: 789 (John Doe, student_id: BCS/234344)
- session_id: 123 (CS201 Lecture, 08:00-10:00)
- time_recorded: 2025-10-25 08:05:00 (5 mins after start)
- latitude: -1.28334000 (student location)
- longitude: 36.81667000
- status: "present"
- is_within_radius: True (distance 15m from session location)

Verification:
✅ Token valid (from email)
✅ QR code scanned: BCS/234344 matches token student
✅ Session active (08:00-10:00, now 08:05)
✅ Within 30m radius (15m < 30m)
✅ Student in correct program
```

### Scenario 2: Late Attendance (Outside Radius)
```
Attendance:
- student_profile_id: 790 (Alice Brown)
- session_id: 123
- time_recorded: 2025-10-25 09:45:00 (near end of session)
- latitude: -1.28400000 (50m away from session)
- longitude: 36.81700000
- status: "late"
- is_within_radius: False (distance 52m > 30m)

Verification:
✅ Token valid
✅ QR code matches
✅ Session active (still within 08:00-10:00 window)
⚠️ Outside 30m radius (52m > 30m)
Result: Attendance recorded with "late" status and flag for lecturer review
```

### Scenario 3: Blocked Attempts (No Record Created)

**Expired Token**:
- Token expired at 09:00
- Student attempts at 09:30
- **Error**: 410 Gone - "Token has expired"
- **No attendance record created**

**QR Code Mismatch (Fraud Attempt)**:
- Token for Student A (BCS/234344)
- QR code scanned: BCS/567890 (Student B's ID)
- **Error**: 400 Bad Request - "QR code does not match token student"
- **No attendance record created**
- **Security**: Prevents email forwarding fraud

**Duplicate Attempt**:
- Student already marked attendance for this session
- **Error**: 409 Conflict - "Attendance already marked"
- **No duplicate record created**

## Migration Considerations

**Priority: HIGH** - Database setup

### Initial Migration
```python
# Pseudo-migration steps
operations = [
    CreateModel(
        name='Attendance',
        fields=[
            ('attendance_id', AutoField(primary_key=True)),
            ('student_profile', ForeignKey(..., on_delete=CASCADE)),
            ('session', ForeignKey(..., on_delete=CASCADE)),
            ('time_recorded', DateTimeField(auto_now_add=True)),
            ('latitude', DecimalField(max_digits=10, decimal_places=8)),
            ('longitude', DecimalField(max_digits=11, decimal_places=8)),
            ('status', CharField(max_length=20)),
            ('is_within_radius', BooleanField()),
        ],
    ),
    AddConstraint(
        model_name='attendance',
        constraint=UniqueConstraint(
            fields=['student_profile', 'session'],
            name='unique_attendance_per_student_session'
        ),
    ),
    AddIndex(model_name='attendance', index=Index(fields=['student_profile'])),
    AddIndex(model_name='attendance', index=Index(fields=['session'])),
    AddIndex(model_name='attendance', index=Index(fields=['time_recorded'])),
    AddIndex(model_name='attendance', index=Index(fields=['status'])),
]
```

### Why No Default Values
- **time_recorded**: auto_now_add sets automatically
- **status**: Must be explicitly determined by service logic
- **is_within_radius**: Must be calculated, not assumed
- **coordinates**: Must come from student device, not defaulted

## Common Query Patterns

**Priority: HIGH** - Optimize these queries

```sql
-- Get all attendance for a session (attendance list)
SELECT * FROM attendance 
WHERE session_id = 123 
ORDER BY time_recorded;

-- Get student's attendance history
SELECT * FROM attendance 
WHERE student_profile_id = 789 
ORDER BY time_recorded DESC;

-- Count present vs late for a session
SELECT status, COUNT(*) 
FROM attendance 
WHERE session_id = 123 
GROUP BY status;

-- Find students outside radius (potential fraud)
SELECT * FROM attendance 
WHERE session_id = 123 
AND is_within_radius = FALSE;

-- Check if attendance exists (duplicate prevention)
SELECT COUNT(*) 
FROM attendance 
WHERE student_profile_id = 789 
AND session_id = 123;

-- Get recent attendance (today)
SELECT * FROM attendance 
WHERE DATE(time_recorded) = CURRENT_DATE 
ORDER BY time_recorded DESC;
```

---

**Status**: 📋 Complete model specification ready for implementation

**Key Takeaways**:
1. **One attendance per student per session** (unique constraint)
2. **Immutable records** (audit trail, no edits allowed)
3. **Three-factor verification** (token, QR, GPS)
4. **GPS stored as Decimal** (precision matters for distance)
5. **CASCADE deletes** (GDPR compliance, referential integrity)
6. **is_within_radius flag** (audit trail, not blocker)