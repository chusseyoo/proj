# Database Entities and Relationships

## Database Schema Overview

This document defines all database entities (tables), their attributes, and the relationships between them.

---

# Entities

## Entity A: User

The User entity represents all system users (Admin, Lecturer, and Student).

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `user_id` | Primary Key | Unique identifier for each user |
| `first_name` | String | User's first name |
| `last_name` | String | User's last name |
| `email` | String | User's email address (unique) |
| `password` | String (nullable) | Hashed password for authentication. Nullable because Student accounts do NOT require passwords; only Admin and Lecturer accounts use this field. |
| `role` | Enum | User role: Admin, Lecturer, or Student |
| `is_active` | Boolean | Account activation status |
| `date_joined` | DateTime | Account creation timestamp |

### Role-Specific Profiles

Users have additional profile information based on their role:

#### LecturerProfile

| Attribute | Type | Description |
|-----------|------|-------------|
| `lecturer_id` | Primary Key | Unique identifier for lecturer |
| `user_id` | Foreign Key | References User table |
| `department_name` | String | Department lecturer belongs to |

#### StudentProfile

| Attribute | Type | Description |
|-----------|------|-------------|
| `student_profile_id` | Primary Key (Integer) | Auto-generated internal identifier |
| `student_id` | String (Unique) | Institutional ID in format `ABC/123456` (e.g., `BCS/234344`) |
| `user_id` | Foreign Key | References User (`user_id`) |
| `program_id` | Foreign Key | References Program (`program_id`) |
| `stream_id` | Foreign Key (nullable) | References Stream (`stream_id`) |
| `year_of_study` | Integer | Current academic year |
| `qr_code_data` | String | Must equal `student_id` (QR contains the same value) |

**Constraints**
- `student_id` unique across system
- Regex: `^[A-Z]{3}/[0-9]{6}$`
- `qr_code_data = student_id`

```sql
-- Schema constraints (reference)
ALTER TABLE student_profiles
  ADD CONSTRAINT valid_student_id_format CHECK (student_id ~ '^[A-Z]{3}/[0-9]{6}$'),
  ADD CONSTRAINT qr_matches_student_id CHECK (qr_code_data = student_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_student_profiles_student_id ON student_profiles(student_id);
```

### Business Rules for StudentProfile

- Students do NOT have passwords (access via email links only)
- `student_id` follows institutional format: `{PROGRAM_CODE}/{NUMBER}`
  - Pattern: 3 uppercase letters + `/` + 6 digits
  - Example: `BCS/234344`, `ENG/123456`, `MED/987654`
- `student_id` must be unique across the entire system
- `qr_code_data` matches `student_id` for verification purposes
- One student can only be in one Program but may be in a specific Stream

### Authentication notes (clarification)

- Students are registered by administrators but DO NOT receive login credentials. The `password` field is intentionally nullable for student accounts.
- Lecturers self-register or request activation; admins may activate or manage lecturer accounts but CANNOT create/register new lecturer accounts directly.

---

## Entity B: Course

Represents academic courses taught in programs.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `course_id` | Primary Key | Unique identifier for course |
| `course_name` | String | Full name of the course |
| `course_code` | String | Course code (e.g., CS101) |
| `program_id` | Foreign Key | References Program table |
| `department_name` | String | Department offering the course |
| `lecturer_id` | Foreign Key | References LecturerProfile table |

---

## Entity C: Session

Represents attendance sessions created by lecturers.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `session_id` | Primary Key | Unique identifier for session |
| `program_id` | Foreign Key | References Program table |
| `course_id` | Foreign Key | References Course table |
| `lecturer_id` | Foreign Key | References LecturerProfile table |
| `stream_id` | Foreign Key | References Stream table (nullable) |
| `date_created` | Date | Date session was created |
| `time_created` | DateTime | Session start time |
| `time_ended` | DateTime | Session end time |
| `latitude` | Decimal | Lecturer's latitude coordinate |
| `longitude` | Decimal | Lecturer's longitude coordinate |

### Business rules (sessions)

- Sessions are created only by Lecturers (Admins cannot create attendance sessions).
- When a session is created the system should generate a short-lived time-limited JWT token (used in emailed links) and enqueue delivery to eligible students. One-time codes are NOT required in the current design.

---

## Entity D: Program

Represents academic programs (e.g., Bachelor of Computer Science).

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `program_id` | Primary Key | Unique identifier for program |
| `program_name` | String | Full name of the program |
| `program_code` | String | Program code abbreviation |
| `department_name` | String | Department offering the program |
| `has_streams` | Boolean | Whether program is divided into streams |

---

## Entity E: Stream

Represents subdivisions within programs (e.g., Stream A, Stream B).

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `stream_id` | Primary Key | Unique identifier for stream |
| `stream_name` | String | Name of the stream |
| `program_id` | Foreign Key | References Program table |
| `year_of_study` | Integer | Year level for this stream |

---

## Entity F: Attendance

Represents individual attendance records.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `attendance_id` | Primary Key | Unique identifier for attendance record |
| `student_id` | Foreign Key | References StudentProfile table |
| `session_id` | Foreign Key | References Session table |
| `time_recorded` | DateTime | When attendance was marked |
| `longitude` | Decimal | Student's longitude when scanning |
| `latitude` | Decimal | Student's latitude when scanning |
| `status` | String | Attendance status (present, late, etc.) |
| `is_within_radius` | Boolean | Whether student was within 30m |

### Constraints

- **UNIQUE(student_id, session_id)** - Ensures one attendance per student per session

Additional behavior:

- The system must validate student eligibility server-side (program/stream membership) and check for duplicates before inserting attendance. The UNIQUE constraint is enforced at the DB level and validated in application logic to return a clear 409 on conflicts.

---

## Entity G: Report

Represents generated attendance reports.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `report_id` | Primary Key | Unique identifier for report |
| `session_id` | Foreign Key | References Session table |
| `generated_by` | Foreign Key | References User table (Admin/Lecturer) |
| `generated_date` | DateTime | When report was generated |
| `file_path` | String | Location of exported file |
| `file_type` | Enum | Format: CSV or Excel |

---

## Entity H: EmailNotification

Minimal email notification for attendance links.

| Attribute | Type | Description |
|-----------|------|-------------|
| `email_id` | Primary Key (Integer) | Unique identifier |
| `session_id` | Foreign Key | References Session (`session_id`) |
| `student_profile_id` | Foreign Key | References StudentProfile (`student_profile_id`) |
| `token` | String | Short-lived JWT for the attendance link |
| `token_expires_at` | DateTime | Token expiration |
| `status` | Enum | `pending`, `sent`, `failed` |
| `created_at` | DateTime | Created/queued time |
| `sent_at` | DateTime (nullable) | When email was sent |

**Constraints**
- UNIQUE (`session_id`, `student_profile_id`)
- FK: ON DELETE CASCADE from Session and StudentProfile

```sql
-- Schema snippet (reference)
CREATE TABLE IF NOT EXISTS email_notifications (
  email_id SERIAL PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  student_profile_id INTEGER NOT NULL REFERENCES student_profiles(student_profile_id) ON DELETE CASCADE,
  token TEXT NOT NULL,
  token_expires_at TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pending','sent','failed')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  sent_at TIMESTAMPTZ,
  UNIQUE (session_id, student_profile_id)
);
```

---

# Entity Relationships

## 1. User ←→ LecturerProfile

**Relationship Type:** One-to-Zero-or-One

```
User (1) ──── (0..1) LecturerProfile
```

### Description
- Each User can have **zero or one** LecturerProfile (only if role = 'Lecturer')
- Each LecturerProfile belongs to **exactly one** User

### Business Rule
- LecturerProfile is created only when user role is "Lecturer"
- One-to-one relationship ensures data integrity

---

## 2. User ←→ StudentProfile

**Relationship Type:** One-to-Zero-or-One

```
User (1) ──── (0..1) StudentProfile
```

### Description
- Each User can have **zero or one** StudentProfile (only if role = 'Student')
- Each StudentProfile belongs to **exactly one** User

### Business Rule
- StudentProfile is created only when user role is "Student"
- **Important:** A User has either LecturerProfile OR StudentProfile OR neither (Admin), never both

---

## 3. Program ←→ Stream

**Relationship Type:** One-to-Many

```
Program (1) ──── (0..*) Stream
```

### Description
- Each Program has **zero or more** Streams
- Each Stream belongs to **exactly one** Program

### Business Rules
- Programs with `has_streams = False` will have **zero** streams
- Programs with `has_streams = True` will have **one or more** streams
- Streams provide subdivision within programs

---

## 4. Program ←→ StudentProfile

**Relationship Type:** One-to-Many

```
Program (1) ──── (1..*) StudentProfile
```

### Description
- Each Program has **one or more** Students enrolled
- Each Student belongs to **exactly one** Program

### Business Rule
- Every student must be enrolled in a program
- Students cannot be enrolled in multiple programs simultaneously

---

## 5. Stream ←→ StudentProfile

**Relationship Type:** One-to-Many (Optional)

```
Stream (1) ──── (0..*) StudentProfile
```

### Description
- Each Stream can have **zero or more** Students
- Each Student may belong to **zero or one** Stream (optional)

### Business Rules
- Students in programs **without streams** will have `stream_id = NULL`
- Students in programs **with streams** must be assigned to a stream

---

## 6. Program ←→ Course

**Relationship Type:** One-to-Many

```
Program (1) ──── (1..*) Course
```

### Description
- Each Program has **one or more** Courses
- Each Course belongs to **exactly one** Program

### Business Rule
- Courses are program-specific
- Programs must have at least one course

---

## 7. LecturerProfile ←→ Course

**Relationship Type:** One-to-Many

```
LecturerProfile (1) ──── (0..*) Course
```

### Description
- Each Lecturer can teach **zero or more** Courses
- Each Course is taught by **exactly one** Lecturer

### Business Rules
- A lecturer may not be assigned to any courses initially
- Each course must have exactly one assigned lecturer
- Courses cannot have multiple lecturers (in this system)

---

## 8. Course ←→ Session

**Relationship Type:** One-to-Many

```
Course (1) ──── (0..*) Session
```

### Description
- Each Course can have **zero or more** Sessions
- Each Session is for **exactly one** Course

### Business Rule
- Sessions are always tied to a specific course
- New courses start with zero sessions

---

## 9. Program ←→ Session

**Relationship Type:** One-to-Many

```
Program (1) ──── (0..*) Session
```

### Description
- Each Program can have **zero or more** Sessions
- Each Session targets **exactly one** Program

### Business Rule
- Sessions must target a specific program
- Used to determine which students receive notifications

---

## 10. Stream ←→ Session

**Relationship Type:** One-to-Many (Optional)

```
Stream (1) ──── (0..*) Session
```

### Description
- Each Stream can have **zero or more** Sessions
- Each Session may target **zero or one** Stream (optional)

### Business Rules
- Sessions can be for **entire programs** (`stream_id = NULL`)
- Sessions can be for **specific streams** (stream_id set)
- Allows flexible targeting of students

---

## 11. LecturerProfile ←→ Session

**Relationship Type:** One-to-Many

```
LecturerProfile (1) ──── (0..*) Session
```

### Description
- Each Lecturer can create **zero or more** Sessions
- Each Session is created by **exactly one** Lecturer

### Business Rule
- Sessions are owned by the lecturer who created them
- Used for access control and reporting

---

## 12. StudentProfile ←→ Attendance

**Relationship Type:** One-to-Many

```
StudentProfile (1) ──── (0..*) Attendance
```

### Description
- Each Student can have **zero or more** Attendance records
- Each Attendance record belongs to **exactly one** Student

### Business Rule
- Students accumulate attendance records over time
- Attendance history is maintained per student

---

## 13. Session ←→ Attendance

**Relationship Type:** One-to-Many

```
Session (1) ──── (0..*) Attendance
```

### Description
- Each Session can have **zero or more** Attendance records
- Each Attendance record belongs to **exactly one** Session

### Business Rule
- **Critical Constraint:** Each student can only have **ONE** attendance record per session
- Enforced by database constraint: `UNIQUE(student_id, session_id)`

---

## 14. Session ←→ Report

**Relationship Type:** One-to-Many

```
Session (1) ──── (0..*) Report
```

### Description
- Each Session can have **zero or more** Reports generated
- Each Report is for **exactly one** Session

### Business Rule
- Multiple reports can be generated for the same session (over time)
- Reports are session-specific snapshots

---

## 15. User ←→ Report

**Relationship Type:** One-to-Many

```
User (1) ──── (0..*) Report
```

### Description
- Each User (Admin/Lecturer) can generate **zero or more** Reports
- Each Report is generated by **exactly one** User

### Business Rule
- Provides audit trail for report generation
- Tracks who generated which reports

---

## 16. Session ←→ EmailNotification

**Relationship Type:** One-to-Many

```
Session (1) ──── (1..*) EmailNotification
```

### Description
- Each Session has **one or more** EmailNotifications (at least one eligible student)
- Each EmailNotification is for **exactly one** Session

### Business Rules
- EmailNotifications are automatically generated when a session is created
- One notification per eligible student (based on program/stream)
- Multiple notifications per session (one for each student)
- A session must have at least one eligible student to be valid
- Minimal tracking: status, created_at, sent_at only

---

## 17. StudentProfile ←→ EmailNotification

**Relationship Type:** One-to-Many

```
StudentProfile (1) ──── (0..*) EmailNotification
```

### Description
- Each Student can have **zero or more** EmailNotifications across sessions
- Each EmailNotification belongs to **exactly one** StudentProfile

### Business Rules
- One notification per student per session (`UNIQUE(session_id, student_id)`)
- Notifications are created only for eligible students (program/stream targeting)
- `EmailNotification.student_id` is a FK to `StudentProfile.student_id`

---

# Relationship Summary Diagram

```
                    ┌──────────┐
                    │   User   │
                    └────┬─────┘
                         │
           ┌─────────────┼─────────────┐
           │             │             │
           ▼             ▼             ▼
    ┌────────────┐  ┌────────────┐   (Admin - no profile)
    │LecturerProf│  │StudentProf │
    └────┬───────┘  └────┬───────┘
         │               │
         │               ├───────────────┐
         │               │               │
    ┌────▼─────┐    ┌────▼─────┐        │
    │  Course  │    │ Program  │        │
    └────┬─────┘    └────┬─────┘        │
         │               │              │
         ▼               ▼              │
      Session <──────── Stream ◄────────┘
         │  ▲
         │  │ (FKs: lecturer_id, course_id, program_id, stream_id     // ...existing code...
     
     # Relationship Summary Diagram
     
     Legend: 1, 0..1, 0..*, 1..*
     
                               ┌──────────┐
                               │   User   │
                               └──┬────┬──┘
                                  │1   │1
                         0..1     │    │     0..1
                        ┌─────────▼┐  ┌▼──────────┐
                        │LecturerPr│  │StudentProf│
                        └─────┬────┘  └────┬──────┘
                              │            │
                              │            │
                              │            │
                              │            │
                              │            │
                              │       ┌────▼─────┐
                              │       │ Program  │
                              │       └──┬───┬───┘
                              │          │   │
                              │        0..* 1..*
                              │          │   │
                          0..*│          │   │0..*
                        ┌─────▼───┐      │ ┌─▼───────┐
                        │  Course │      │ │  Stream │
                        └────┬────┘      │ └──┬──────┘
                             │1          │    │0..1
                             └────┬──────┴────┬───┐
                                  │              │
                                  ▼              │
                              ┌──────────┐       │
                              │  Session │◄──────┘
                              └─┬──┬──┬──┘
                                │  │  │
                             0..*│  │ 0..*
                                │  │
                                ▼  ▼
                         ┌────────┐   ┌────────────────┐
                         │Attend. │   │EmailNotification│
                         └──┬─────┘   └──────┬─────────┘
                            │               │
                        0..*│               │ 1..*
                            │               │
                            ▼               ▲
                       ┌──────────┐         │
                       │StudentPro│─────────┘
                       └──────────┘
     
                                   0..*
                     ┌──────────────────────────┐
                     │         Report           │
                     └──┬───────────────────┬───┘
                        │1                  │1
                        ▼                   ▼
                     Session              User
     
     // ...existing code...)
         │
   ┌─────┴──────┐
   │ Attendance │
   └─────┬──────┘
         │
         ▼
       Report (FK: session_id, generated_by → User)

             ┌──────────────────────┐
             │   EmailNotification  │
             └───────────┬──────────┘
                         ▲│
       (0..*)            ││ (1..*)
StudentProfile ──────────┘└────────── Session
     (FK: student_id)              (FK: session_id)
```

---

# Key Design Principles

## 1. User Role Segregation
- Users are polymorphic (Admin, Lecturer, Student)
- Role-specific data stored in separate profile tables
- The `password` column in User is nullable. Authentication is required only for Admins and Lecturers; Student records are kept without login credentials.
- Role assignment determines which profile row is created (LecturerProfile or StudentProfile)

## 2. Program/Stream Flexibility
- Not all programs have streams (`has_streams` flag)
- Sessions and Students can optionally target specific streams
- Nullable `stream_id` allows program-wide or stream-specific operations
- Supports both flat and hierarchical organizational structures

## 3. Attendance Constraints
- One student can only mark attendance once per session
- Database constraint: `UNIQUE(student_id, session_id)`
- Prevents duplicate attendance records
- Maintains data integrity

## 4. Location-Based Validation
- Sessions store lecturer's location (latitude, longitude)
- Attendance records store student's scan location
- `is_within_radius` field validates 30m proximity requirement
- Both locations preserved for audit purposes

## 5. Reporting and Audit Trail
- Reports tied to specific sessions
- Track who generated each report (`generated_by`)
- Support multiple export formats (CSV/Excel)
- Historical record of report generation
- Maintains accountability

## 6. Referential Integrity
- All foreign keys maintain referential integrity
- Cascading deletes should be carefully considered
- Orphaned records prevented through constraints
- Data consistency guaranteed at database level

## 7. Email Notification System
- Automated email notifications sent when sessions are created
- JWT tokens embedded in email links for secure, time-limited access
- Status tracking (pending, sent, failed) for delivery monitoring
- Asynchronous queue processing for scalability
- One email per eligible student per session

---

# Database Constraints Summary

| Constraint Type | Entity | Description |
|----------------|--------|-------------|
| PRIMARY KEY | All entities | Unique identifier for each record |
| FOREIGN KEY | All relationships | Maintains referential integrity |
| UNIQUE | Attendance | `(student_id, session_id)` - One attendance per student per session |
| UNIQUE | EmailNotification | `(session_id, student_id)` - One email per student per session |
| NOT NULL | Most fields | Ensures required data is provided |
| CHECK | User.role | Must be Admin, Lecturer, or Student |
| CHECK | Report.file_type | Must be CSV or Excel |
| CHECK | Program.has_streams | Boolean value |
| CHECK | EmailNotification.status | Must be pending, sent, or failed |

---

# DDL Statements

## 1. User Table

```sql
CREATE TABLE users (
  user_id SERIAL PRIMARY KEY,
  first_name VARCHAR(50) NOT NULL,
  last_name VARCHAR(50) NOT NULL,
  email VARCHAR(100) NOT NULL UNIQUE,
  password VARCHAR(255),  -- Nullable for Students
  role VARCHAR(10) NOT NULL CHECK (role IN ('Admin', 'Lecturer', 'Student')),
  is_active BOOLEAN DEFAULT TRUE,
  date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 2. LecturerProfile Table

```sql
CREATE TABLE lecturer_profiles (
  lecturer_id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  department_name VARCHAR(100) NOT NULL
);
```

## 3. StudentProfile Table

```sql
CREATE TABLE student_profiles (
  student_profile_id SERIAL PRIMARY KEY,  -- Auto-generated for DB relations
  student_id VARCHAR(20) NOT NULL UNIQUE,  -- Business ID: BCS/234344
  user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  program_id INTEGER NOT NULL REFERENCES programs(program_id),
  stream_id INTEGER REFERENCES streams(stream_id),
  year_of_study INTEGER NOT NULL CHECK (year_of_study BETWEEN 1 AND 4),
  qr_code_data VARCHAR(20) NOT NULL,  -- Matches student_id
  CONSTRAINT valid_student_id_format CHECK (student_id ~ '^[A-Z]{3}/[0-9]{6}$'),
  CONSTRAINT qr_matches_student_id CHECK (qr_code_data = student_id)
);

CREATE INDEX idx_student_profiles_student_id ON student_profiles(student_id);
CREATE INDEX idx_student_profiles_user_id ON student_profiles(user_id);
CREATE INDEX idx_student_profiles_program_stream ON student_profiles(program_id, stream_id);
```

## 4. Programs Table

```sql
CREATE TABLE programs (
  program_id SERIAL PRIMARY KEY,
  program_name VARCHAR(100) NOT NULL,
  program_code VARCHAR(10) NOT NULL UNIQUE,
  department_name VARCHAR(100) NOT NULL,
  has_streams BOOLEAN DEFAULT FALSE
);
```

## 5. Streams Table

```sql
CREATE TABLE streams (
  stream_id SERIAL PRIMARY KEY,
  stream_name VARCHAR(50) NOT NULL,
  program_id INTEGER NOT NULL REFERENCES programs(program_id) ON DELETE CASCADE,
  year_of_study INTEGER NOT NULL CHECK (year_of_study BETWEEN 1 AND 4)
);
```

## 6. Courses Table

```sql
CREATE TABLE courses (
  course_id SERIAL PRIMARY KEY,
  course_name VARCHAR(100) NOT NULL,
  course_code VARCHAR(10) NOT NULL,
  program_id INTEGER NOT NULL REFERENCES programs(program_id) ON DELETE CASCADE,
  department_name VARCHAR(100) NOT NULL,
  lecturer_id INTEGER REFERENCES lecturer_profiles(lecturer_id) ON DELETE SET NULL
);
```

## 7. Sessions Table

```sql
CREATE TABLE sessions (
  session_id SERIAL PRIMARY KEY,
  program_id INTEGER NOT NULL REFERENCES programs(program_id) ON DELETE CASCADE,
  course_id INTEGER NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
  lecturer_id INTEGER NOT NULL REFERENCES lecturer_profiles(lecturer_id) ON DELETE CASCADE,
  stream_id INTEGER REFERENCES streams(stream_id) ON DELETE SET NULL,
  date_created DATE NOT NULL,
  time_created TIMESTAMP NOT NULL,
  time_ended TIMESTAMP NOT NULL,
  latitude DECIMAL(9,6) NOT NULL,
  longitude DECIMAL(9,6) NOT NULL
);
```

## 8. Attendance Table

```sql
CREATE TABLE attendance (
  attendance_id SERIAL PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES student_profiles(student_profile_id) ON DELETE CASCADE,
  session_id INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  time_recorded TIMESTAMP NOT NULL,
  longitude DECIMAL(9,6) NOT NULL,
  latitude DECIMAL(9,6) NOT NULL,
  status VARCHAR(10) NOT NULL,
  is_within_radius BOOLEAN NOT NULL,

  CONSTRAINT unique_student_session UNIQUE (student_id, session_id)
);
```

## 9. Reports Table

```sql
CREATE TABLE reports (
  report_id SERIAL PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  generated_by INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  file_path VARCHAR(255) NOT NULL,
  file_type VARCHAR(10) NOT NULL CHECK (file_type IN ('CSV', 'Excel'))
);
```

## 10. EmailNotifications Table

```sql
CREATE TABLE email_notifications (
  email_id SERIAL PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  student_id INTEGER NOT NULL REFERENCES student_profiles(student_profile_id) ON DELETE CASCADE,
  token VARCHAR(255) NOT NULL,
  token_expires_at TIMESTAMP NOT NULL,
  status VARCHAR(10) NOT NULL CHECK (status IN ('pending', 'sent', 'failed')),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  sent_at TIMESTAMP
);
```