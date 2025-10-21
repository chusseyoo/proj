# Service Layer Guide - Complete System Service Architecture

**Last Updated**: October 21, 2025  
**Purpose**: Comprehensive overview of all service layers across bounded contexts

---

## Overview

This document provides a system-wide view of all services across bounded contexts. Services encapsulate business logic, orchestrate workflows, enforce validation rules, and coordinate between repositories and external systems.

---

## System-Wide Service Conventions

### Service Types
1. **Domain Services** - Pure business logic, no infrastructure dependencies
2. **Application Services** - Orchestrate use cases, coordinate domain services and repositories
3. **Integration Services** - Handle cross-context communication
4. **Infrastructure Services** - Adapt external systems (SMTP, JWT, file systems)

### Common Patterns
- **Dependency Injection**: Services receive dependencies via constructor
- **Error Handling**: Services throw domain exceptions, caught and mapped by API layer
- **Transaction Management**: Use case services manage transaction boundaries
- **Authorization**: Services enforce role-based access control before operations
- **Validation**: Input validation at service entry points, business rules in domain services

### Standard Service Structure
```
{Context}Service
├── Dependencies (repositories, domain services, external adapters)
├── Public Methods (use cases)
│   ├── Input validation
│   ├── Authorization checks
│   ├── Business logic orchestration
│   ├── Repository calls
│   └── Return DTOs
└── Private helpers
```

---

## Services by Bounded Context

### 1. User Management

**Base Path**: `user_management/domain/services/`, `user_management/application/use_cases/`

#### Domain Services

**IdentityService**
- **Purpose**: Handle authentication, password hashing, token generation
- **Key Methods**:
  - `authenticate(email, password)` → User | AuthenticationError
  - `hash_password(plain_password)` → hashed_string
  - `verify_password(plain, hashed)` → bool
  - `generate_reset_token(user)` → token_string
- **Priority**: CRITICAL (security foundation)
- **Dependencies**: Password hasher adapter, token generator

**EnrollmentService**
- **Purpose**: Student and lecturer enrollment business rules
- **Key Methods**:
  - `validate_student_eligibility(student_profile, program)` → bool
  - `check_enrollment_conflicts(student, courses)` → conflicts[]
- **Priority**: HIGH
- **Dependencies**: Academic Structure integration

#### Application Services (Use Cases)

**CreateUser**
- **Purpose**: User registration workflow
- **Flow**:
  1. Validate email format (Email value object)
  2. Check email uniqueness
  3. Hash password (IdentityService)
  4. Create User entity
  5. Persist via UserRepository
  6. Create profile (Student/Lecturer) if applicable
  7. Send welcome email (Email Notifications context)
- **Authorization**: Public (registration) or Admin (manual creation)
- **Errors**: DuplicateEmailError, InvalidEmailError, WeakPasswordError

**UpdateProfile**
- **Purpose**: Update student/lecturer profile
- **Flow**:
  1. Authorize (user can only update own profile, or admin)
  2. Fetch profile
  3. Validate changes
  4. Update via repository
  5. Return DTO
- **Authorization**: Self or Admin

**DeactivateUser**
- **Purpose**: Soft-delete user account
- **Flow**:
  1. Authorize (Admin only)
  2. Check dependencies (active sessions, pending reports)
  3. Set is_active=False
  4. Cascade to profiles
- **Authorization**: Admin only
- **Priority**: HIGH (data integrity)

---

### 2. Academic Structure

**Base Path**: `academic_structure/application/use_cases/`

#### ProgramService
- **Purpose**: Manage academic programs
- **Key Methods**:
  - `create_program(data)` → ProgramDTO
  - `update_program(id, data)` → ProgramDTO
  - `delete_program(id)` → void (checks for courses/students)
  - `list_programs(filters, page, page_size)` → Paginated[ProgramDTO]
- **Validations**:
  - Unique program_code (case-insensitive)
  - Code uppercase enforcement
  - Cannot delete if has courses or enrolled students
- **Priority**: HIGH
- **Reference**: [`docs/contexts/academic-structure/services_guide.md`](docs/contexts/academic-structure/services_guide.md)

#### StreamService
- **Purpose**: Manage program streams (specializations)
- **Key Methods**:
  - `create_stream(data)` → StreamDTO
  - `list_by_program(program_id)` → StreamDTO[]
  - `delete_stream(id)` → void (checks for enrolled students)
- **Validations**:
  - Program must have has_streams=True
  - Unique (program, year_of_study, stream_name)
  - Year range: 1-4
- **Priority**: MEDIUM

#### CourseService
- **Purpose**: Manage courses
- **Key Methods**:
  - `create_course(data)` → CourseDTO
  - `assign_lecturer(course_id, lecturer_id)` → CourseDTO
  - `list_by_program(program_id)` → CourseDTO[]
- **Validations**:
  - Unique course_code
  - Lecturer must be active
  - Course belongs to program
- **Priority**: HIGH

---

### 3. Session Management

**Base Path**: `session_management/application/use_cases/`

#### SessionService
- **Purpose**: Create and manage attendance sessions
- **Key Methods**:
  - `create_session(lecturer_id, payload)` → SessionDTO
  - `update_session(session_id, lecturer_id, updates)` → SessionDTO
  - `end_now(session_id, lecturer_id, now)` → SessionDTO
  - `get_session(session_id, lecturer_id)` → SessionDTO
  - `list_my_sessions(lecturer_id, filters, page, page_size)` → Paginated[SessionDTO]
- **Validations**:
  - Lecturer must own the course
  - Lecturer must be active
  - Program/stream targeting rules (stream must belong to program)
  - Time window: time_ended > time_created (10m to 24h duration)
  - No overlapping sessions for same lecturer
  - GPS coordinates within valid ranges
- **Authorization**: Lecturer only (owns sessions)
- **Priority**: CRITICAL (core workflow entry point)
- **Cross-Context**:
  - Triggers Email Notifications (SessionCreated event)
  - Validates with Academic Structure (Program, Course, Stream)
  - Validates with User Management (Lecturer active and ownership)
- **Reference**: [`docs/contexts/session-management/services_guide.md`](docs/contexts/session-management/services_guide.md)

---

### 4. Attendance Recording

**Base Path**: `attendance_recording/domain/services/`, `attendance_recording/application/use_cases/`

#### Domain Services (Validators)

**TokenValidator**
- **Purpose**: Validate JWT tokens from emails
- **Key Methods**:
  - `validate_token(token)` → TokenPayload | TokenError
  - `decode_token(token)` → claims_dict
  - `check_expiry(claims)` → bool
- **Validations**:
  - Signature verification (HS256)
  - Expiry check
  - Required claims: student_profile_id, session_id, exp
- **Priority**: CRITICAL (security)

**QRCodeValidator**
- **Purpose**: Validate scanned QR codes (anti-fraud)
- **Key Methods**:
  - `validate_qr_code(qr_data)` → student_id | QRError
  - `check_format(qr_data)` → bool
  - `match_student(qr_student_id, token_student_id)` → bool
- **Validations**:
  - Format: `^[A-Z]{3}/[0-9]{6}$`
  - QR student_id must match token student_id
  - Log mismatch as fraud attempt
- **Priority**: CRITICAL (anti-fraud)

**LocationValidator**
- **Purpose**: Validate GPS proximity (Haversine distance)
- **Key Methods**:
  - `validate_location(student_lat, student_lng, session_lat, session_lng)` → bool
  - `calculate_distance(lat1, lng1, lat2, lng2)` → meters (Haversine)
- **Validations**:
  - Distance <= 30 meters (inclusive)
  - Haversine formula for accuracy
- **Priority**: CRITICAL (physical presence)

**SessionValidator**
- **Purpose**: Validate session eligibility and time window
- **Key Methods**:
  - `validate_session(session, student_profile)` → void | SessionError
  - `check_active_window(session, now)` → bool
  - `check_eligibility(student, session)` → bool
- **Validations**:
  - Session exists and not cancelled
  - Session is active (time_created <= now < time_ended)
  - Student belongs to session's program/stream target
- **Priority**: CRITICAL

#### Application Service

**AttendanceService**
- **Purpose**: Orchestrate attendance marking (10-step workflow)
- **Key Method**:
  - `mark_attendance(token, qr_code, latitude, longitude)` → AttendanceDTO
- **Workflow**:
  1. Validate token (TokenValidator)
  2. Decode token → student_profile_id, session_id
  3. Validate QR code format (QRCodeValidator)
  4. Match QR student_id with token student_id (anti-fraud)
  5. Fetch session (SessionRepository)
  6. Validate session active and not cancelled (SessionValidator)
  7. Check student eligibility (SessionValidator)
  8. Validate GPS proximity (LocationValidator)
  9. Check for duplicate attendance (AttendanceRepository)
  10. Create attendance record with status and is_within_radius flag
- **Authorization**: Token-based (no role check; token proves eligibility)
- **Priority**: CRITICAL (main user workflow)
- **Errors**: 14 domain exceptions (TokenExpiredError, QRMismatchError, LocationTooFarError, etc.)
- **Reference**: [`docs/contexts/attendance-recording/services_guide.md`](docs/contexts/attendance-recording/services_guide.md)

---

### 5. Email Notifications

**Base Path**: `email_notifications/domain/services/`, `email_notifications/application/use_cases/`

#### Domain Services

**JWTTokenService**
- **Purpose**: Generate and validate JWT tokens for attendance links
- **Key Methods**:
  - `generate_token(student_profile_id, session_id, expiry_minutes)` → token_string
  - `validate_token(token)` → claims_dict | InvalidTokenError
  - `decode_token(token)` → claims_dict
- **Token Structure**:
  - Algorithm: HS256
  - Claims: student_profile_id, session_id, exp (expiry timestamp)
  - Expiry: 30-60 minutes (configurable)
- **Priority**: CRITICAL (security)

**TemplateService**
- **Purpose**: Generate email content from templates
- **Key Methods**:
  - `render_session_notification(student, session, token)` → (subject, html_body, text_body)
- **Priority**: MEDIUM

#### Application Services

**NotificationGenerationService**
- **Purpose**: Orchestrate bulk notification creation
- **Key Method**:
  - `generate_for_session(session_id)` → NotificationDTO[]
- **Workflow**:
  1. Fetch session details (Session Management)
  2. Fetch eligible students (Academic Structure: program/stream targeting)
  3. For each student:
     - Generate JWT token (JWTTokenService)
     - Render email template (TemplateService)
     - Create EmailNotification record (pending status)
  4. Bulk create via EmailNotificationRepository
  5. Trigger async send (EmailSenderService)
- **Priority**: HIGH
- **Reference**: [`docs/contexts/email-notifications/services_guide.md`](docs/contexts/email-notifications/services_guide.md)

**EmailSenderService**
- **Purpose**: Send emails via SMTP
- **Key Methods**:
  - `send_email(notification_id)` → void
  - `retry_failed(notification_id)` → void
- **Flow**:
  1. Fetch notification
  2. Send via SMTP adapter
  3. Update status (sent/failed) and sent_at
  4. Log errors for retry
- **Priority**: HIGH
- **Infrastructure**: Async (Celery or similar)

---

### 6. Reporting

**Base Path**: `reporting/application/use_cases/`, `reporting/domain/services/`

#### Domain Services

**AttendanceAggregator**
- **Purpose**: Classify students as Present/Late/Absent
- **Key Method**:
  - `aggregate_attendance(session, eligible_students, attendance_records)` → AggregatedData
- **Classification Logic**:
  - **Present**: status="present" AND is_within_radius=True
  - **Late**: status="late" OR is_within_radius=False
  - **Absent**: No attendance record exists
- **Priority**: CRITICAL (reporting accuracy)

**StatisticsCalculator**
- **Purpose**: Compute attendance percentages
- **Key Methods**:
  - `calculate_percentages(present, late, absent, total)` → percentages_dict
- **Priority**: MEDIUM

#### Application Services

**ReportService**
- **Purpose**: Generate and manage reports
- **Key Methods**:
  - `generate_report(session_id, user_id)` → ReportDTO (view-only, no file)
  - `get_report(report_id, user_id)` → ReportDTO (real-time data)
  - `list_reports(user_id, filters, page, page_size)` → Paginated[ReportDTO]
- **Authorization**:
  - Lecturer: Only own sessions' reports
  - Admin: All reports
- **Priority**: HIGH
- **Reference**: [`docs/contexts/reporting/services_guide.md`](docs/contexts/reporting/services_guide.md)

**ExportService**
- **Purpose**: Export reports to CSV/Excel
- **Key Method**:
  - `export_report(report_id, user_id, format)` → file_path
- **Flow**:
  1. Authorize (lecturer or admin)
  2. Check if already exported (immutability)
  3. Fetch report data (AttendanceAggregator)
  4. Generate file (CSV/Excel adapter)
  5. Update report with file_path and file_type
  6. Return file_path
- **File Structure**:
  - Path: `/media/reports/{year}/{month}/session_{id}_{timestamp}.{ext}`
  - CSV: Header comments + data rows
  - Excel: Formatted with color-coded status, bold headers
- **Priority**: MEDIUM
- **Immutability**: Cannot re-export (409 Conflict)

---

## Cross-Context Service Integration

### Key Integration Points

1. **Session Creation Flow**
   - Session Management → Email Notifications
   - Trigger: `create_session()` emits SessionCreated event
   - Email Notifications: `generate_for_session()` creates bulk notifications

2. **Attendance Marking Flow**
   - Attendance Recording validates against:
     - Email Notifications (token validity)
     - Session Management (session exists, active)
     - Academic Structure (student eligibility)
     - User Management (student active)

3. **Report Generation Flow**
   - Reporting queries:
     - Session Management (session details)
     - Academic Structure (eligible students)
     - Attendance Recording (attendance records)
     - User Management (student/lecturer names)

### Service Communication Patterns

**Synchronous (Direct Calls)**
- Used for: Validation, authorization, data fetching
- Example: AttendanceService → SessionRepository.get_by_id()

**Event-Driven (Async)**
- Used for: Notifications, long-running tasks
- Example: SessionService emits SessionCreated → EmailNotificationService listens

**API-to-API (REST)**
- Used for: Cross-context queries when direct DB access violates boundaries
- Example: Reporting calls Academic Structure API for eligible students

---

## Service Error Handling

### Standard Domain Exceptions by Context

**User Management**
- `DuplicateEmailError` (409)
- `UserNotFoundError` (404)
- `AuthenticationError` (401)
- `WeakPasswordError` (400)

**Academic Structure**
- `ProgramNotFoundError` (404)
- `DuplicateProgramCodeError` (409)
- `CannotDeleteProgramError` (409 - has courses/students)

**Session Management**
- `SessionNotFoundError` (404)
- `OverlappingSessionError` (409)
- `InvalidTimeWindowError` (400)
- `AuthorizationError` (403 - not session owner)

**Attendance Recording**
- `TokenExpiredError` (410)
- `TokenInvalidError` (401)
- `QRMismatchError` (403 - fraud attempt)
- `LocationTooFarError` (425)
- `SessionNotActiveError` (410 - too early) / (425 - too late)
- `DuplicateAttendanceError` (409)
- `StudentNotEligibleError` (403)

**Email Notifications**
- `NotificationNotFoundError` (404)
- `AlreadySentError` (409)
- `SMTPError` (500)

**Reporting**
- `ReportNotFoundError` (404)
- `AlreadyExportedError` (409)
- `UnauthorizedReportAccessError` (403)

### Error Mapping to HTTP Status Codes

| Domain Exception | HTTP Status | User Message |
|-----------------|-------------|--------------|
| NotFoundError | 404 | Resource not found |
| DuplicateError | 409 | Already exists |
| ValidationError | 400 | Invalid input |
| AuthorizationError | 403 | Not authorized |
| AuthenticationError | 401 | Invalid credentials |
| ExpiredError | 410 | Resource expired |
| TooEarlyError | 425 | Too early, try again later |
| InfrastructureError | 500 | Internal error, contact support |

---

## Service Testing Strategy

### Unit Tests (Domain Services)
- Test business logic in isolation
- Mock all dependencies (repositories, external adapters)
- Focus on: validation rules, calculations, state transitions
- Example: TokenValidator → test expiry logic with mocked time

### Integration Tests (Application Services)
- Test orchestration with real repositories (test DB)
- Mock only cross-context calls and external systems (SMTP, file system)
- Focus on: workflows, transaction boundaries, error propagation
- Example: AttendanceService → test full workflow with test DB

### Contract Tests (Cross-Context)
- Verify service contracts between contexts
- Use shared DTOs/interfaces
- Example: Email Notifications expects SessionCreated event with {session_id, program_id, stream_id}

---

## Service Performance Considerations

### Optimization Patterns

1. **Bulk Operations** (Email Notifications)
   - Use `bulk_create()` for notifications (1 query vs N queries)
   - Priority: HIGH (performance for large classes)

2. **Caching** (Academic Structure)
   - Cache program/course lookups (rarely change)
   - Invalidate on update
   - Priority: MEDIUM

3. **Pagination** (All list operations)
   - Default page_size: 20, max: 100
   - Use cursor-based pagination for large datasets
   - Priority: HIGH

4. **Query Optimization** (Reporting)
   - Use `select_related()` for foreign keys
   - Use `prefetch_related()` for many-to-many
   - Aggregate in DB when possible
   - Priority: HIGH

5. **Async Processing** (Email Notifications)
   - Send emails asynchronously (Celery)
   - Batch sends (e.g., 50 emails/minute to avoid rate limits)
   - Priority: CRITICAL (user experience)

---

## Quick Reference: Core Services

| Context | Service | Primary Method | Priority | Cross-Context Dependencies |
|---------|---------|----------------|----------|---------------------------|
| User Management | IdentityService | authenticate() | CRITICAL | None |
| User Management | CreateUser | create_user() | HIGH | Email Notifications |
| Academic Structure | ProgramService | create_program() | HIGH | None |
| Academic Structure | CourseService | assign_lecturer() | HIGH | User Management |
| Session Management | SessionService | create_session() | CRITICAL | Academic Structure, User Management, Email Notifications |
| Attendance Recording | AttendanceService | mark_attendance() | CRITICAL | Email Notifications, Session Management, Academic Structure, User Management |
| Email Notifications | NotificationGenerationService | generate_for_session() | HIGH | Session Management, Academic Structure |
| Email Notifications | EmailSenderService | send_email() | HIGH | SMTP (external) |
| Reporting | ReportService | generate_report() | HIGH | Session Management, Academic Structure, Attendance Recording |
| Reporting | ExportService | export_report() | MEDIUM | File system (external) |

---

## Implementation Order

**Phase 1: Foundation**
1. User Management (IdentityService, CreateUser)
2. Academic Structure (ProgramService, CourseService)

**Phase 2: Core Workflow**
3. Session Management (SessionService)
4. Email Notifications (JWTTokenService, NotificationGenerationService)

**Phase 3: User Actions**
5. Attendance Recording (Validators + AttendanceService)

**Phase 4: Analytics**
6. Reporting (ReportService, ExportService)

---

## Additional Resources

For detailed implementation guides, see:
- User Management: [`docs/contexts/user-management/services_guide.md`](docs/contexts/user-management/services_guide.md)
- Academic Structure: [`docs/contexts/academic-structure/services_guide.md`](docs/contexts/academic-structure/services_guide.md)
- Session Management: [`docs/contexts/session-management/services_guide.md`](docs/contexts/session-management/services_guide.md)
- Attendance Recording: [`docs/contexts/attendance-recording/services_guide.md`](docs/contexts/attendance-recording/services_guide.md)
- Email Notifications: [`docs/contexts/email-notifications/services_guide.md`](docs/contexts/email-notifications/services_guide.md)
- Reporting: [`docs/contexts/reporting/services_guide.md`](docs/contexts/reporting/services_guide.md)

---

**Status**: ✅ Complete service architecture documented across all bounded contexts