# Bounded Contexts Overview

This document provides a high-level overview of all bounded contexts in the QR-based Attendance Management System.

## System Architecture

The system is organized into **6 bounded contexts** plus a **shared documentation folder**:

```
/docs
  /user-management/          # User accounts, authentication, authorization
  /academic-structure/       # Programs, streams, courses
  /session-management/       # Session creation by lecturers
  /email-notifications/      # Email delivery with JWT tokens
  /attendance-recording/     # QR verification, location validation, attendance marking
  /reporting/                # Report generation and export
  /shared/                   # Cross-cutting documentation
```

---

## 1. User Management Context

**Purpose**: Manage user accounts, authentication, and authorization

**Core Entities**:
- User (user_id, email, password*, role, is_active)
- LecturerProfile (lecturer_id, user_id, department_name)
- StudentProfile (student_profile_id, student_id, user_id, program_id, stream_id*, year_of_study, qr_code_data)

**Key Features**:
- Admin: Full system access
- Lecturer: Self-registration, auto-activated, manage own resources
- Student: Registered by admin, no password (passwordless via JWT)

**Important Notes**:
- Password is nullable (NULL for students)
- Student ID format: `ABC/123456` (e.g., `BCS/234344`)
- QR code data matches student ID

**Integration**:
- Called by: All contexts (to validate users, get user data)
- Calls: Academic Structure (validate program_id, stream_id)

---

## 2. Academic Structure Context

**Purpose**: Manage academic organizational structure

**Core Entities**:
- Program (program_id, program_name, program_code, has_streams)
- Stream (stream_id, stream_name, program_id, year_of_study)
- Course (course_id, course_name, course_code, program_id, lecturer_id*)

**Key Features**:
- Programs can have streams (has_streams flag)
- One lecturer per course
- Admin-only management

**Important Notes**:
- `program_code` is 3 letters (used in student IDs)
- `stream_id` nullable (NULL if program has no streams)
- `lecturer_id` nullable in Course (can be unassigned initially)

**Integration**:
- Called by: User Management (validate program/stream), Session Management (validate course/program)
- Calls: User Management (validate lecturer_id)

---

## 3. Session Management Context

**Purpose**: Handle session creation and configuration

**Core Entities**:
- Session (session_id, program_id, course_id, lecturer_id, stream_id*, date_created, time_created, time_ended, latitude, longitude)

**Key Features**:
- Only assigned lecturer can create session for course
- Capture lecturer's GPS location
- Target entire program or specific stream
- Time window validation

**Important Notes**:
- `stream_id` nullable (targets entire program if NULL)
- Session creation triggers email notification generation
- Lecturer location used for 30m radius check during attendance

**Integration**:
- Called by: Attendance Recording (get session details), Reporting (get session metadata)
- Calls: Academic Structure (validate course/program/stream), User Management (validate lecturer), Email Notifications (trigger generation)

---

## 4. Email Notifications Context

**Purpose**: Generate and send email notifications with JWT tokens

**Core Entities**:
- EmailNotification (email_id, session_id, student_profile_id, token, token_expires_at, status, created_at, sent_at*)

**Key Features**:
- Generate JWT tokens for attendance links
- Track email delivery status (pending, sent, failed)
- Asynchronous background processing
- One email per student per session

**Important Notes**:
- `sent_at` nullable (NULL until sent)
- JWT token contains: `{student_profile_id, session_id, exp}`
- Token is short-lived (30-60 minutes)
- Recipient email NOT stored (fetched from User.email at send time)

**Integration**:
- Called by: Session Management (trigger generation), Attendance Recording (validate token)
- Calls: User Management (get student emails), Session Management (get session details), Academic Structure (get course info)

---

## 5. Attendance Recording Context

**Purpose**: Mark attendance with three-factor verification

**Core Entities**:
- Attendance (attendance_id, student_profile_id, session_id, time_recorded, latitude, longitude, status, is_within_radius)

**Key Features**:
- JWT token validation
- QR code verification (anti-fraud)
- 30m radius location validation (Haversine formula)
- Duplicate prevention (UNIQUE constraint)
- Student eligibility validation

**Important Notes**:
- Three-factor verification: Token + QR + GPS
- QR mismatch prevents fraud (someone using another's email)
- `is_within_radius` calculated and stored (not editable)
- One attendance per student per session

**Integration**:
- Called by: Reporting (query attendance records)
- Calls: Email Notifications (validate token), Session Management (get session details), User Management (get student details)

---

## 6. Reporting Context

**Purpose**: Generate and export attendance reports

**Core Entities**:
- Report (report_id, session_id, generated_by, generated_date, file_path*, file_type*)

**Key Features**:
- View reports online
- Export to CSV or Excel
- Present/Late/Absent classification
- Lecturer sees own reports, Admin sees all

**Important Notes**:
- `file_path` and `file_type` nullable (NULL if not exported)
- Multiple reports can exist for same session (historical snapshots)
- Attendance status inferred: Present (attended + within radius), Late (attended but issues), Absent (no record)

**Integration**:
- Calls: Session Management (get session details), User Management (get student list), Attendance Recording (get attendance records), Academic Structure (get course info)

---

## Cross-Context Data Flow

### Session Creation Flow
```
1. Lecturer → Session Management: Create session
2. Session Management → Academic Structure: Validate course/program/stream
3. Session Management → User Management: Validate lecturer
4. Session Management: Save session
5. Session Management → Email Notifications: Trigger email generation
6. Email Notifications → User Management: Get eligible students
7. Email Notifications: Create EmailNotification records (status=pending)
8. Email Notifications: Queue background task
9. Background Worker: Send emails (update status to sent/failed)
```

### Attendance Marking Flow
```
1. Student clicks email link → Attendance Recording: Mark attendance
2. Attendance Recording → Email Notifications: Validate JWT token
3. Attendance Recording → Session Management: Get session details
4. Attendance Recording → User Management: Get student details
5. Attendance Recording: Verify QR code matches student
6. Attendance Recording: Validate session time window
7. Attendance Recording: Validate student eligibility (program/stream)
8. Attendance Recording: Calculate distance (30m radius)
9. Attendance Recording: Check duplicate
10. Attendance Recording: Save attendance record
```

### Report Generation Flow
```
1. Lecturer/Admin → Reporting: Generate report
2. Reporting → Session Management: Get session details
3. Reporting → User Management: Get eligible students list
4. Reporting → Attendance Recording: Query attendance records
5. Reporting: Classify students (Present/Late/Absent)
6. Reporting: Create Report record
7. Reporting: Display report online OR export to file
```

---

## Nullable Attributes Summary

| Entity | Nullable Attributes | Reason |
|--------|---------------------|--------|
| User | `password` | Students don't have passwords |
| StudentProfile | `stream_id` | Programs may not have streams |
| Course | `lecturer_id` | Can be unassigned initially |
| Session | `stream_id` | Can target entire program |
| EmailNotification | `sent_at` | NULL until email is sent |
| Report | `file_path`, `file_type` | NULL if not exported |

---

## Key Design Principles

1. **Separation of Concerns**: Each context has clear boundaries
2. **Explicit Dependencies**: Contexts call each other through well-defined interfaces
3. **Nullable by Design**: Nullable fields handle optional/conditional data
4. **Security by Default**: Three-factor verification for attendance
5. **Audit Trail**: All actions tracked (who, when, where)
6. **Idempotency**: Duplicate prevention (UNIQUE constraints)
7. **Background Processing**: Email sending doesn't block session creation
8. **Stateless Tokens**: JWT tokens are self-contained, no server-side session
9. **Location Privacy**: GPS coordinates stored for audit but not publicly displayed
10. **Flexible Structure**: Supports programs with/without streams

---

## Implementation Order

For each context, follow this order:

1. **Models** - Define data structure and constraints
2. **Repositories** - Implement data access layer
3. **Services** - Implement business logic
4. **Handlers** - Orchestrate application flow
5. **Views/Serializers** - Implement API endpoints
6. **Permissions** - Implement access control
7. **Tests** - Comprehensive testing

Start with contexts that have fewer dependencies:

1. **User Management** (few dependencies)
2. **Academic Structure** (depends on User Management)
3. **Session Management** (depends on Academic Structure + User Management)
4. **Email Notifications** (depends on Session Management)
5. **Attendance Recording** (depends on all above)
6. **Reporting** (depends on all above)

---

## Next Steps

1. **Review all context READMEs** to understand scope and entities
2. **Verify nullable attributes** match your requirements
3. **Confirm integration points** between contexts
4. **Choose a context to start** (recommend User Management)
5. **Read detailed guides** in implementation order
6. **Implement context by context** - don't implement all at once

---

**Status**: 📝 All Context Overviews Complete - Ready to start detailed implementation guides

---

## Files Location

- User Management: `/docs/user-management/README.md`
- Academic Structure: `/docs/academic-structure/README.md`
- Session Management: `/docs/session-management/README.md`
- Email Notifications: `/docs/email-notifications/README.md`
- Attendance Recording: `/docs/attendance-recording/README.md`
- Reporting: `/docs/reporting/README.md`
- This Overview: `/docs/shared/BOUNDED_CONTEXTS_OVERVIEW.md`
