# Models Guide - Complete System Data Model Reference

This document provides a comprehensive overview of all Django models across the QR Code-Based Attendance Management System, organized by bounded context. Each context has its own detailed models guide; this serves as a central reference for understanding the complete data model, relationships, and cross-context dependencies.

---

## System-Wide Model Conventions

### Naming Conventions
- **Table names**: Lowercase plural (e.g., `users`, `sessions`, `attendance`)
- **Primary keys**: `{model_name}_id` (e.g., `user_id`, `session_id`, `attendance_id`)
- **Foreign keys**: Referenced model name (e.g., `user`, `session`, `program`)
- **Boolean fields**: Prefix with `is_` or `has_` (e.g., `is_active`, `has_streams`)

### Field Types
- **IDs**: AutoField (auto-increment integers)
- **Strings**: CharField with max_length
- **Text**: TextField for long content
- **Numbers**: IntegerField, DecimalField
- **Dates/Times**: DateTimeField with timezone support
- **Booleans**: BooleanField with defaults
- **Foreign Keys**: ForeignKey with on_delete behavior

### Delete Behaviors
- **CASCADE**: Delete dependent records (e.g., User → StudentProfile)
- **PROTECT**: Prevent deletion if dependents exist (e.g., Program with enrolled students)
- **SET_NULL**: Set to NULL on deletion (e.g., Stream deleted → Student.stream = NULL)

### Validation Approach
- **Database level**: CHECK constraints, UNIQUE constraints
- **Model level**: `clean()` method for complex validation
- **Service level**: Business logic validation (cross-context checks)

---

## Data Model by Bounded Context

### 1. User Management Context

**Purpose**: User authentication, profiles (students, lecturers, admins)

**Models**: User, StudentProfile, LecturerProfile

---

#### Model: User

**Purpose**: Core user entity for all system users (authentication model)

**Table**: `users`

**Key Fields**:
- `user_id`: AutoField (PK)
- `first_name`: CharField(50)
- `last_name`: CharField(50)
- `email`: EmailField(255, unique=True)
- `password`: CharField(255, **nullable for students**)
- `role`: CharField(20, choices=['Admin', 'Lecturer', 'Student'])
- `is_active`: BooleanField(default=True)
- `date_joined`: DateTimeField(auto_now_add=True)

**Key Constraints**:
- Email must be unique (case-insensitive)
- Students cannot have passwords (NULL)
- Admin/Lecturer must have passwords (NOT NULL)

**Indexes**:
- `email` (for login lookups)
- `role` (for role filtering)

**Methods**:
- `get_full_name()` → str
- `is_student()` → bool
- `is_lecturer()` → bool
- `is_admin()` → bool

**Relationships**:
- One-to-one with StudentProfile (if role='Student')
- One-to-one with LecturerProfile (if role='Lecturer')

---

#### Model: StudentProfile

**Purpose**: Extended profile for students with academic information

**Table**: `student_profiles`

**Key Fields**:
- `student_profile_id`: AutoField (PK)
- `student_id`: CharField(20, unique=True, format: `ABC/123456`)
- `user`: OneToOneField(User, CASCADE)
- `program`: ForeignKey(Program, PROTECT)
- `stream`: ForeignKey(Stream, SET_NULL, nullable)
- `year_of_study`: IntegerField(1-4)
- `qr_code_data`: CharField(20, must equal student_id)

**Key Constraints**:
- student_id format: `^[A-Z]{3}/[0-9]{6}$`
- qr_code_data must equal student_id
- Stream required if program.has_streams=True
- Stream must be NULL if program.has_streams=False
- User must have role='Student'

**Indexes**:
- `student_id` (unique)
- `user_id`
- Composite: `(program, stream)`

**Validation**:
- Student ID format checked on save
- QR code auto-set to student_id
- Stream validation based on program configuration

**Relationships**:
- Belongs to User (one-to-one)
- Belongs to Program (many-to-one)
- Belongs to Stream (many-to-one, optional)
- Has many Attendance records
- Has many EmailNotifications

---

#### Model: LecturerProfile

**Purpose**: Extended profile for lecturers

**Table**: `lecturer_profiles`

**Key Fields**:
- `lecturer_id`: AutoField (PK)
- `user`: OneToOneField(User, CASCADE)
- `department_name`: CharField(100)

**Key Constraints**:
- User must have role='Lecturer'

**Indexes**:
- `user_id`

**Relationships**:
- Belongs to User (one-to-one)
- Has many Courses (assigned)
- Has many Sessions (created)

**For Details**: See `/docs/contexts/user-management/models_guide.md`

---

### 2. Academic Structure Context

**Purpose**: Programs, courses, streams, cohorts

**Models**: Program, Stream, Course

---

#### Model: Program

**Purpose**: Academic degree programs

**Table**: `programs`

**Key Fields**:
- `program_id`: AutoField (PK)
- `program_name`: CharField(200, unique=True)
- `program_code`: CharField(3, unique=True, format: `ABC`)
- `department_name`: CharField(100)
- `has_streams`: BooleanField(default=False)

**Key Constraints**:
- program_code format: `^[A-Z]{3}$` (exactly 3 uppercase letters)
- program_code unique
- program_name unique

**Indexes**:
- `program_code`
- `department_name`

**Methods**:
- `can_be_deleted()` → bool (checks for students/courses)
- `get_stream_count()` → int

**Validation**:
- Program code auto-converted to uppercase
- Cannot delete if students enrolled or courses exist

**Relationships**:
- Has many Streams (one-to-many)
- Has many Courses (one-to-many)
- Has many StudentProfiles (cross-context)
- Has many Sessions (cross-context)

---

#### Model: Stream

**Purpose**: Subdivisions within programs (optional)

**Table**: `streams`

**Key Fields**:
- `stream_id`: AutoField (PK)
- `stream_name`: CharField(100)
- `program`: ForeignKey(Program, CASCADE)
- `year_of_study`: IntegerField(1-4)

**Key Constraints**:
- Unique together: `(program, stream_name, year_of_study)`
- Parent program must have `has_streams=True`
- year_of_study between 1 and 4

**Indexes**:
- `program`
- `year_of_study`

**Methods**:
- `get_student_count()` → int
- `can_be_deleted()` → bool

**Relationships**:
- Belongs to Program (many-to-one)
- Has many StudentProfiles (cross-context)
- Has many Sessions (cross-context, optional)

---

#### Model: Course

**Purpose**: Individual courses offered in programs

**Table**: `courses`

**Key Fields**:
- `course_id`: AutoField (PK)
- `course_name`: CharField(200)
- `course_code`: CharField(10, unique=True, format: `ABC123`)
- `program`: ForeignKey(Program, CASCADE)
- `department_name`: CharField(100)
- `lecturer`: ForeignKey(LecturerProfile, SET_NULL, nullable)

**Key Constraints**:
- course_code format: `^[A-Z]{2,4}[0-9]{3}$`
- course_code unique
- Lecturer must be active if assigned

**Indexes**:
- `course_code`
- `program`
- `lecturer`

**Methods**:
- `is_assigned_to_lecturer()` → bool
- `get_lecturer_name()` → str
- `can_be_deleted()` → bool

**Validation**:
- Course code auto-converted to uppercase
- Cannot delete if sessions exist
- Lecturer must be active when assigning

**Relationships**:
- Belongs to Program (many-to-one)
- Belongs to LecturerProfile (many-to-one, optional)
- Has many Sessions (cross-context)

**For Details**: See `/docs/contexts/academic-structure/models_guide.md`

---

### 3. Session Management Context

**Purpose**: Lecturers create attendance sessions

**Models**: Session

---

#### Model: Session

**Purpose**: Time-bounded attendance session with location

**Table**: `sessions`

**Key Fields**:
- `session_id`: AutoField (PK)
- `program`: ForeignKey(Program, CASCADE)
- `course`: ForeignKey(Course, CASCADE)
- `lecturer`: ForeignKey(LecturerProfile, PROTECT)
- `stream`: ForeignKey(Stream, SET_NULL, nullable)
- `time_created`: DateTimeField (session start)
- `time_ended`: DateTimeField (session end)
- `latitude`: DecimalField(10, 8, range: -90 to 90)
- `longitude`: DecimalField(11, 8, range: -180 to 180)
- `location_description`: CharField(100, nullable)

**Key Constraints**:
- time_ended > time_created
- latitude in [-90, 90]
- longitude in [-180, 180]
- If program.has_streams=False, stream must be NULL
- If stream provided, it must belong to program
- No overlapping sessions for same lecturer

**Indexes**:
- `course_id`
- `lecturer_id`
- Composite: `(program_id, stream_id)`
- Composite: `(time_created, time_ended)`

**Derived Status** (not stored):
- `created`: record exists
- `active`: now in [time_created, time_ended)
- `ended`: now ≥ time_ended

**Validation** (service-enforced):
- Lecturer must be active and assigned to course
- Course must belong to program
- Duration: 10 minutes to 24 hours
- No overlapping sessions for lecturer

**Relationships**:
- Belongs to Program (many-to-one)
- Belongs to Course (many-to-one)
- Belongs to LecturerProfile (many-to-one)
- Belongs to Stream (many-to-one, optional)
- Has many Attendance records
- Has many EmailNotifications
- Has many Reports

**For Details**: See `/docs/contexts/session-management/models_guide.md`

---

### 4. Attendance Recording Context

**Purpose**: Students mark attendance with three-factor verification

**Models**: Attendance

---

#### Model: Attendance

**Purpose**: Record verified student attendance with location proof

**Table**: `attendance`

**Key Fields**:
- `attendance_id`: AutoField (PK)
- `student_profile`: ForeignKey(StudentProfile, CASCADE)
- `session`: ForeignKey(Session, CASCADE)
- `time_recorded`: DateTimeField(auto_now_add=True)
- `latitude`: DecimalField(10, 8)
- `longitude`: DecimalField(11, 8)
- `status`: CharField(20, choices=['present', 'late'])
- `is_within_radius`: BooleanField

**Key Constraints**:
- **UNIQUE**: `(student_profile, session)` - one attendance per student per session
- latitude in [-90, 90]
- longitude in [-180, 180]
- **Immutable**: Cannot be updated after creation

**Indexes**:
- `student_profile_id`
- `session_id`
- `time_recorded`
- `status`
- Composite: `(session_id, status)` (for reporting)

**Status Determination**:
- `present`: On time AND within 30m radius
- `late`: Outside radius OR near end of session

**Validation** (service-layer):
- Token valid (JWT)
- QR code matches token student (fraud prevention)
- Session is active
- Student eligible (program/stream match)
- No duplicate attendance
- GPS coordinates valid
- Calculate distance (Haversine)

**Methods**:
- `is_late()` → bool
- `is_present()` → bool
- `get_distance_from_session()` → float
- `was_on_time()` → bool

**Relationships**:
- Belongs to StudentProfile (many-to-one)
- Belongs to Session (many-to-one)

**Security Features**:
- Three-factor verification (token + QR + GPS)
- Immutable records (audit trail)
- Duplicate prevention (unique constraint)
- Fraud detection (QR mismatch logged)

**For Details**: See `/docs/contexts/attendance-recording/models_guide.md`

---

### 5. Email Notifications Context

**Purpose**: Send attendance notification emails with JWT tokens

**Models**: EmailNotification

---

#### Model: EmailNotification

**Purpose**: Track email notifications with JWT tokens

**Table**: `email_notifications`

**Key Fields**:
- `email_id`: AutoField (PK)
- `session`: ForeignKey(Session, CASCADE)
- `student_profile`: ForeignKey(StudentProfile, CASCADE)
- `token`: TextField (JWT string)
- `token_expires_at`: DateTimeField
- `status`: CharField(20, choices=['pending', 'sent', 'failed'])
- `created_at`: DateTimeField(auto_now_add=True)
- `sent_at`: DateTimeField(nullable)

**Key Constraints**:
- **UNIQUE**: `(session, student_profile)` - one email per student per session
- token_expires_at > created_at
- sent_at only set when status='sent'

**Indexes**:
- `session_id`
- `student_profile_id`
- `status`
- `token`

**Status Workflow**:
- `pending`: Created, queued, not yet sent
- `sent`: Successfully delivered to SMTP server
- `failed`: Delivery attempt failed

**Status Transitions**:
- `pending` → `sent` ✅ (normal flow)
- `pending` → `failed` ✅ (delivery error)
- `failed` → `pending` ✅ (retry)
- `sent` → any ❌ (sent is final)

**Methods**:
- `is_expired()` → bool
- `is_sent()` → bool
- `can_retry()` → bool
- `mark_as_sent(timestamp)` → void
- `mark_as_failed()` → void

**Relationships**:
- Belongs to Session (many-to-one)
- Belongs to StudentProfile (many-to-one)

**Workflow**:
1. Session created → Generate notifications (status='pending')
2. Background worker picks up pending notifications
3. Send email → Update status to 'sent', set sent_at
4. On failure → Update status to 'failed'
5. Admin can retry failed notifications

**For Details**: See `/docs/contexts/email-notifications/models_guide.md`

---

### 6. Reporting Context

**Purpose**: Generate and export attendance reports

**Models**: Report

---

#### Model: Report

**Purpose**: Metadata for attendance reports with optional file export

**Table**: `reports`

**Key Fields**:
- `report_id`: AutoField (PK)
- `session`: ForeignKey(Session, CASCADE)
- `generated_by`: ForeignKey(User, PROTECT)
- `generated_date`: DateTimeField(auto_now_add=True)
- `file_path`: CharField(500, nullable)
- `file_type`: CharField(10, choices=['csv', 'excel'], nullable)

**Key Constraints**:
- **CHECK**: `(file_type IS NULL AND file_path IS NULL) OR (file_type IS NOT NULL AND file_path IS NOT NULL)`
- No unique constraint (multiple reports per session allowed)

**Indexes**:
- `session_id`
- `generated_by`
- `generated_date`

**Nullable Fields**:
- `file_path`: NULL for view-only reports, path string for exported
- `file_type`: NULL for view-only, 'csv' or 'excel' for exported

**Validation**:
- file_path and file_type must be synchronized (both NULL or both set)
- generated_by must be session owner (lecturer) or admin

**Immutability**:
- Metadata fields immutable (report_id, session_id, generated_by, generated_date)
- Export fields set once (NULL → value, but not value → different value)

**Methods**:
- `is_exported()` → bool
- `can_be_exported()` → bool

**Relationships**:
- Belongs to Session (many-to-one, CASCADE)
- Belongs to User (many-to-one, PROTECT)

**Use Cases**:
- View-only report: file_path=NULL, file_type=NULL
- CSV export: file_path='/media/...', file_type='csv'
- Excel export: file_path='/media/...', file_type='excel'

**Authorization**:
- Lecturer: Can view/export reports for own sessions
- Admin: Can view/export any report

**For Details**: See `/docs/contexts/reporting/models_guide.md`

---

## Cross-Context Relationships

### User Management ↔ Academic Structure

**StudentProfile → Program**:
- Relationship: Many students per program
- Delete: PROTECT (cannot delete program with students)
- Access: `student.program`, `program.students.all()`

**StudentProfile → Stream**:
- Relationship: Many students per stream (optional)
- Delete: SET_NULL (stream deleted → student.stream = NULL)
- Access: `student.stream`, `stream.students.all()`

**Course → LecturerProfile**:
- Relationship: Many courses per lecturer (optional)
- Delete: SET_NULL (lecturer deleted → course.lecturer = NULL)
- Access: `course.lecturer`, `lecturer.courses.all()`

---

### Academic Structure ↔ Session Management

**Session → Program**:
- Relationship: Many sessions per program
- Delete: CASCADE
- Access: `session.program`, `program.sessions.all()`

**Session → Course**:
- Relationship: Many sessions per course
- Delete: CASCADE
- Access: `session.course`, `course.sessions.all()`

**Session → Stream**:
- Relationship: Many sessions per stream (optional)
- Delete: SET_NULL
- Access: `session.stream`, `stream.sessions.all()`

---

### User Management ↔ Session Management

**Session → LecturerProfile**:
- Relationship: Many sessions per lecturer
- Delete: PROTECT (cannot delete lecturer with sessions)
- Access: `session.lecturer`, `lecturer.sessions.all()`

---

### Session Management ↔ Attendance Recording

**Attendance → Session**:
- Relationship: Many attendance records per session
- Delete: CASCADE
- Access: `attendance.session`, `session.attendance_records.all()`

---

### User Management ↔ Attendance Recording

**Attendance → StudentProfile**:
- Relationship: Many attendance records per student
- Delete: CASCADE
- Access: `attendance.student_profile`, `student.attendance_records.all()`

---

### Session Management ↔ Email Notifications

**EmailNotification → Session**:
- Relationship: Many notifications per session
- Delete: CASCADE
- Access: `notification.session`, `session.email_notifications.all()`

---

### User Management ↔ Email Notifications

**EmailNotification → StudentProfile**:
- Relationship: Many notifications per student
- Delete: CASCADE
- Access: `notification.student_profile`, `student.email_notifications.all()`

---

### Session Management ↔ Reporting

**Report → Session**:
- Relationship: Many reports per session
- Delete: CASCADE
- Access: `report.session`, `session.reports.all()`

---

### User Management ↔ Reporting

**Report → User** (generated_by):
- Relationship: Many reports per user
- Delete: PROTECT (audit trail)
- Access: `report.generated_by`, `user.generated_reports.all()`

---

## Complete Entity Relationship Diagram (Text)

```
User (users)
├── One-to-One: StudentProfile (if role='Student')
├── One-to-One: LecturerProfile (if role='Lecturer')
└── One-to-Many: Report (generated_by, PROTECT)

StudentProfile (student_profiles)
├── Belongs-to: User (CASCADE)
├── Belongs-to: Program (PROTECT)
├── Belongs-to: Stream (SET_NULL, nullable)
├── Has-Many: Attendance (CASCADE)
└── Has-Many: EmailNotification (CASCADE)

LecturerProfile (lecturer_profiles)
├── Belongs-to: User (CASCADE)
├── Has-Many: Course (assigned, SET_NULL)
└── Has-Many: Session (PROTECT)

Program (programs)
├── Has-Many: Stream (CASCADE)
├── Has-Many: Course (CASCADE)
├── Has-Many: StudentProfile (PROTECT)
└── Has-Many: Session (CASCADE)

Stream (streams)
├── Belongs-to: Program (CASCADE)
├── Has-Many: StudentProfile (SET_NULL)
└── Has-Many: Session (SET_NULL)

Course (courses)
├── Belongs-to: Program (CASCADE)
├── Belongs-to: LecturerProfile (SET_NULL, nullable)
└── Has-Many: Session (CASCADE)

Session (sessions)
├── Belongs-to: Program (CASCADE)
├── Belongs-to: Course (CASCADE)
├── Belongs-to: LecturerProfile (PROTECT)
├── Belongs-to: Stream (SET_NULL, nullable)
├── Has-Many: Attendance (CASCADE)
├── Has-Many: EmailNotification (CASCADE)
└── Has-Many: Report (CASCADE)

Attendance (attendance)
├── Belongs-to: StudentProfile (CASCADE)
└── Belongs-to: Session (CASCADE)
└── UNIQUE: (student_profile, session)

EmailNotification (email_notifications)
├── Belongs-to: Session (CASCADE)
├── Belongs-to: StudentProfile (CASCADE)
└── UNIQUE: (session, student_profile)

Report (reports)
├── Belongs-to: Session (CASCADE)
└── Belongs-to: User (generated_by, PROTECT)
```

---

## Key Database Constraints Summary

### Unique Constraints
- `User.email` (case-insensitive)
- `StudentProfile.student_id`
- `Program.program_code`
- `Program.program_name`
- `Stream`: UNIQUE TOGETHER (program, stream_name, year_of_study)
- `Course.course_code`
- `Attendance`: UNIQUE TOGETHER (student_profile, session)
- `EmailNotification`: UNIQUE TOGETHER (session, student_profile)

### Check Constraints
- `User.password`: NULL if role='Student', NOT NULL otherwise
- `StudentProfile.student_id`: Format `^[A-Z]{3}/[0-9]{6}$`
- `StudentProfile.qr_code_data = student_id`
- `StudentProfile.year_of_study`: BETWEEN 1 AND 4
- `Program.program_code`: Format `^[A-Z]{3}$`
- `Stream.year_of_study`: BETWEEN 1 AND 4
- `Course.course_code`: Format `^[A-Z]{2,4}[0-9]{3}$`
- `Session.time_ended > time_created`
- `Session.latitude`: BETWEEN -90 AND 90
- `Session.longitude`: BETWEEN -180 AND 180
- `Attendance.latitude`: BETWEEN -90 AND 90
- `Attendance.longitude`: BETWEEN -180 AND 180
- `EmailNotification.token_expires_at > created_at`
- `Report`: (file_type IS NULL AND file_path IS NULL) OR (file_type IS NOT NULL AND file_path IS NOT NULL)

### Cascade Rules Summary

**CASCADE Deletes** (dependent records deleted):
- User → StudentProfile
- User → LecturerProfile
- Program → Stream
- Program → Course
- Program → Session
- Course → Session
- Session → Attendance
- Session → EmailNotification
- Session → Report
- StudentProfile → Attendance
- StudentProfile → EmailNotification

**PROTECT Deletes** (prevents deletion):
- Program with enrolled students (StudentProfile.program)
- LecturerProfile with sessions (Session.lecturer)
- User with reports (Report.generated_by)

**SET_NULL Deletes** (sets foreign key to NULL):
- Stream → StudentProfile.stream
- LecturerProfile → Course.lecturer
- Stream → Session.stream

---

## Common Query Patterns

### User & Profiles
```sql
-- Get student with profile
SELECT * FROM users u 
JOIN student_profiles sp ON u.user_id = sp.user_id 
WHERE u.role = 'Student' AND u.is_active = TRUE;

-- Get lecturer with courses
SELECT * FROM lecturer_profiles lp 
JOIN courses c ON lp.lecturer_id = c.lecturer_id;
```

### Academic Structure
```sql
-- Get programs with streams
SELECT * FROM programs p 
LEFT JOIN streams s ON p.program_id = s.program_id 
WHERE p.has_streams = TRUE;

-- Get courses by program
SELECT * FROM courses 
WHERE program_id = 1 
ORDER BY course_code;
```

### Sessions & Attendance
```sql
-- Get active sessions
SELECT * FROM sessions 
WHERE NOW() BETWEEN time_created AND time_ended;

-- Get session attendance list
SELECT * FROM attendance a 
JOIN student_profiles sp ON a.student_profile_id = sp.student_profile_id 
WHERE a.session_id = 123;

-- Get attendance statistics
SELECT 
  status, 
  COUNT(*) as count,
  COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
FROM attendance 
WHERE session_id = 123 
GROUP BY status;
```

### Email Notifications
```sql
-- Get pending emails to send
SELECT * FROM email_notifications 
WHERE status = 'pending' 
ORDER BY created_at ASC 
LIMIT 100;

-- Get failed notifications for retry
SELECT * FROM email_notifications 
WHERE status = 'failed';
```

### Reporting
```sql
-- Get reports by lecturer
SELECT * FROM reports r 
JOIN sessions s ON r.session_id = s.session_id 
WHERE s.lecturer_id = 17 
ORDER BY r.generated_date DESC;

-- Get exported reports
SELECT * FROM reports 
WHERE file_path IS NOT NULL;
```

---

## Migration Strategy

### Migration Order
1. **User Management**: User, StudentProfile, LecturerProfile
2. **Academic Structure**: Program, Stream, Course
3. **Session Management**: Session
4. **Attendance Recording**: Attendance
5. **Email Notifications**: EmailNotification
6. **Reporting**: Report

### Dependencies
- StudentProfile depends on User, Program, Stream
- LecturerProfile depends on User
- Stream depends on Program
- Course depends on Program, LecturerProfile
- Session depends on Program, Course, LecturerProfile, Stream
- Attendance depends on StudentProfile, Session
- EmailNotification depends on Session, StudentProfile
- Report depends on Session, User

### Initial Data Requirements
- At least one Admin user
- Sample programs and courses for testing
- Sample students and lecturers for testing

---

## Context-Specific Model Documentation

For detailed model specifications, field definitions, validation rules, and implementation details, refer to the models guide in each context folder:

- **User Management**: `/docs/contexts/user-management/models_guide.md`
- **Academic Structure**: `/docs/contexts/academic-structure/models_guide.md`
- **Session Management**: `/docs/contexts/session-management/models_guide.md`
- **Attendance Recording**: `/docs/contexts/attendance-recording/models_guide.md`
- **Email Notifications**: `/docs/contexts/email-notifications/models_guide.md`
- **Reporting**: `/docs/contexts/reporting/models_guide.md`

---

## Quick Reference

### Primary Entities by Context

| Context | Models | Primary Keys | Key Relationships |
|---------|--------|--------------|-------------------|
| User Management | User, StudentProfile, LecturerProfile | user_id, student_profile_id, lecturer_id | User ↔ Profile (one-to-one) |
| Academic Structure | Program, Stream, Course | program_id, stream_id, course_id | Program → Stream/Course |
| Session Management | Session | session_id | Session → Program/Course/Lecturer/Stream |
| Attendance Recording | Attendance | attendance_id | Attendance → Student/Session |
| Email Notifications | EmailNotification | email_id | Email → Session/Student |
| Reporting | Report | report_id | Report → Session/User |

### Most Referenced Models
1. **Session** - Referenced by Attendance, EmailNotification, Report
2. **StudentProfile** - Referenced by Attendance, EmailNotification
3. **Program** - Referenced by StudentProfile, Course, Session
4. **User** - Referenced by StudentProfile, LecturerProfile, Report

---

**Status**: ✅ Complete system-wide models reference  
**Last Updated**: October 21, 2025