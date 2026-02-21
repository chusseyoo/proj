
# QR Code-Based Attendance Management System

## Project Overview

A comprehensive Django-based attendance management system designed for educational institutions. This system streamlines attendance tracking using QR codes, GPS location validation, and email-based student authentication, eliminating manual attendance taking and reducing proxy attendance fraud.

### Core Purpose

Enable lecturers to quickly create attendance sessions, automatically notify students via email with secure links, and allow students to mark attendance through QR code scanning with GPS verification—all within a 30-minute window per session.

---

## 🎯 Key Features

- **Automated Attendance Tracking**: Lecturers create sessions; emails are sent automatically to eligible students
- **Three-Factor Verification**: JWT token + QR code + GPS location validation ensures secure attendance marking
- **30-Meter Radius Validation**: GPS-based location verification prevents remote attendance marking
- **Passwordless Student Access**: Students authenticate via time-limited JWT tokens in email links
- **Location-Based Eligibility**: Sessions target entire programs or specific streams
- **Complete Audit Trail**: All attendance marked with timestamps and GPS coordinates
- **Flexible Organization**: Supports programs with or without stream subdivisions
- **Data Export**: Generate attendance reports in CSV or Excel formats

---

## 🏗️ System Architecture

The system is organized into **6 bounded contexts** plus **shared infrastructure**, following Domain-Driven Design principles:

```
Project Structure:
├── user_management/          → User accounts, authentication, authorization
├── academic_structure/       → Programs, streams, courses
├── session_management/       → Session creation by lecturers
├── email_notifications/      → Email delivery with JWT tokens
├── attendance_recording/     → QR verification, location validation, attendance marking
└── reporting/                → Report generation and export
```

### Architecture Layers (Per Context)

Each bounded context implements Clean Architecture with 4 layers:

```
Presentation Layer
   ↓ (HTTP requests/responses, API endpoints, serializers)
Application Layer
   ↓ (Use case orchestration, handlers, commands, DTOs)
Domain Layer
   ↓ (Business logic, entities, value objects, domain services)
Infrastructure Layer
   ↓ (Database, external services, JWT, email, repositories)
Database
```

---

## 📚 Core Bounded Contexts

### 1. User Management Context

**Purpose**: Manage user accounts, authentication, and authorization

**Entities**:
- **User**: Universal user entity with three roles
  - `email` (unique, required)
  - `password` (nullable—NULL for students who use passwordless authentication)
  - `role`: `Admin`, `Lecturer`, or `Student`
  - `is_active`: Account activation status
  
- **LecturerProfile**: Profile extension for lecturers
  - One-to-one relationship with User
  - `department_name`: Department/Faculty affiliation
  - Auto-activated on registration (no admin approval needed)
  
- **StudentProfile**: Profile extension for students
  - One-to-one relationship with User
  - `student_id`: Institutional ID in format `ABC/123456` (e.g., `BCS/234344`)
  - `program_id`: Enrolled program
  - `stream_id`: Optional stream within program (nullable if program has no streams)
  - `year_of_study`: Academic year (1-4)
  - `qr_code_data`: Must match `student_id` (enforced by database constraint)

**Business Rules**:
- Lecturers self-register and are automatically activated
- Students registered by admin only; no password required
- Admins have full system access
- Lecturers can only access their own courses and sessions
- Students access system only via email links with JWT tokens

**Key Constraint**: `student_id` format `^[A-Z]{3}/[0-9]{6}$` matches the program code prefix

---

### 2. Academic Structure Context

**Purpose**: Manage academic organizational structure

**Entities**:
- **Program**: Academic degree program
  - `program_name`: Full name (e.g., "Bachelor of Computer Science")
  - `program_code`: 3-letter code (e.g., "BCS", "ENG", "MED")—used as student ID prefix
  - `has_streams`: Boolean flag indicating if program has stream subdivisions
  - `department_name`: Offering department
  
- **Stream**: Subdivision within a program
  - `stream_name`: Name (e.g., "Stream A", "Morning Batch")
  - `program_id`: Parent program
  - `year_of_study`: Academic year for this stream (1-4)
  - Only created if parent program `has_streams = True`
  
- **Course**: Individual course taught in a program
  - `course_name`: Course title
  - `course_code`: 6-character code (`^[A-Z]{3}[0-9]{3}$`, e.g., "BCS201")
  - `program_id`: Program offering the course
  - `lecturer_id`: Assigned lecturer (nullable initially, required for active teaching)

**Business Rules**:
- Each program is either streamed or non-streamed; cannot change after creation
- Lecturers assigned to courses one-per-course
- Only assigned lecturer can create sessions for a course
- Course can be deleted only if no sessions exist

**Integration**:
- User Management validates lecturer IDs when assigning to courses
- Session Management validates courses and programs when creating sessions
- Attendance Recording validates student program/stream eligibility

---

### 3. Session Management Context

**Purpose**: Handle session creation and lifecycle

**Entities**:
- **Session**: Attendance session created by a lecturer
  - `program_id`: Target program
  - `course_id`: Course session is for
  - `lecturer_id`: Session creator (must be assigned to the course)
  - `stream_id`: Optional target stream (nullable = entire program)
  - `date_created`: Creation date
  - `time_created`: Session start time
  - `time_ended`: Session end time (always `time_created + 30 minutes`)
  - `latitude`, `longitude`: Lecturer's GPS coordinates at session creation

**Business Rules**:
- **Session Duration**: Fixed at 30 minutes (cannot be changed)
- **Authorization**: Only the lecturer assigned to the course can create sessions
- **Stream Targeting**:
  - If program `has_streams = False`: `stream_id` must be NULL (entire program targeted)
  - If program `has_streams = True`: `stream_id` can be NULL (entire program) or specific stream
- **Time Window**: Fixed 30-minute duration matching token expiry and attendance marking window
- **Email Trigger**: Session creation automatically queues email notifications to eligible students

**Eligible Students**:
- Program matches session program
- If `stream_id` set: student's stream must match
- Student account active

**Side Effects**:
1. Session saved to database
2. Email Notification Context triggered to generate and queue emails

---

### 4. Email Notifications Context

**Purpose**: Generate and send email notifications with secure attendance links

**Entities**:
- **EmailNotification**: Email sent to a student for a session
  - `session_id`: Target session
  - `student_profile_id`: Recipient student
  - `token`: JWT token for attendance link
  - `token_expires_at`: Token expiration (30 minutes from session start)
  - `status`: Delivery status (`pending`, `sent`, `failed`)
  - `created_at`: When notification was queued
  - `sent_at`: Nullable—set when email successfully sent (NULL while pending/failed)

**Business Rules**:
- One email per student per session (enforced by UNIQUE constraint)
- **JWT Token Structure**:
  - Contains: `{student_profile_id, session_id, exp}`
  - Expires: 30 minutes from session creation
  - Algorithm: HS256 (HMAC-SHA256)
  - Cannot be forged (server-side secret key)
  
- **Email Delivery**:
  - Asynchronous background processing (doesn't block session creation)
  - Recipient email fetched from User table at send time (not stored)
  - Email body generated dynamically with course/session details
  - Status transitions: `pending` → `sent` or `failed`
  
- **Background Processing**: Celery/task queue sends emails asynchronously

**Email Content**:
- Attendance link: `https://yourdomain.com/attendance?token={jwt}`
- Course name, date, time
- Location and 30-meter radius requirement
- Token expiry time

---

### 5. Attendance Recording Context

**Purpose**: Mark attendance with three-factor verification

**Entities**:
- **Attendance**: Single attendance record
  - `student_profile_id`: Student marking attendance
  - `session_id`: Session attended
  - `time_recorded`: When marked (server timestamp, not client)
  - `latitude`, `longitude`: Student's GPS coordinates
  - `status`: Attendance status (`present` or `late`)
  - `is_within_radius`: Boolean flag (true if within 30m)

**Three-Factor Verification** (all must pass):

1. **JWT Token** (What you received):
   - Verify token signature
   - Check expiry (30 minutes from session start)
   - Extract `student_profile_id` and `session_id`

2. **QR Code** (What you have):
   - Scanned student ID in format `ABC/123456`
   - Must match student linked to token
   - Prevents email forwarding fraud

3. **GPS Location** (Where you are):
   - Must be within 30 meters of session location
   - Calculated using Haversine formula
   - Prevents remote attendance marking

**Attendance Status Determination**:

- **present**: Marked within first 30 minutes of session start AND within 30m radius
- **late**: Marked after first 30 minutes OR outside 30m radius (or both)
  - Still recorded but flagged as late
  - Outside-radius attempts still create attendance record (for audit)

**Workflow**:
1. Student clicks email link with JWT token
2. Token decoded and validated
3. QR code scanned and verified against token student
4. Session validated (exists, active, student eligible)
5. GPS coordinates provided and distance calculated
6. Attendance record created with status and `is_within_radius` flag
7. Duplicate check prevents marking twice for same session

**Duplicate Prevention**: UNIQUE constraint on `(student_profile_id, session_id)` prevents multiple records

---

### 6. Reporting Context

**Purpose**: Generate and export attendance reports

**Entities**:
- **Report**: Generated attendance report
  - `session_id`: Session being reported
  - `generated_by`: User who generated report
  - `generated_date`: When report was generated
  - `file_path`: Nullable—path to exported file (if exported to CSV/Excel)
  - `file_type`: Nullable—export format (`csv` or `excel`)

**Business Rules**:
- Multiple reports can exist for same session (historical snapshots)
- Reports are view-only initially (no file until exported)

**Access Control**:
- **Lecturer**: Can generate/view reports only for own sessions
- **Admin**: Can generate/view reports for all sessions
- **Student**: No access to reporting

**Attendance Classification**:
- **Present**: Attendance record exists with `status = "present"`
- **Late**: Attendance record with `status = "late"` OR no record exists
  - Students without attendance records classified as late (not separate "absent" category)

**Report Content** (CSV/Excel):
- Student ID, Name, Email
- Program, Stream (if applicable)
- Attendance Status (Present/Late)
- Time Recorded (if marked)
- Within Radius? (Yes/No, if marked)
- GPS coordinates (if marked, for audit)

**Report Header**:
- Session metadata (ID, course, program, stream)
- Session date/time
- Lecturer name
- Report generation date/user
- Statistics: Total students, Present count/%, Late count/%

**Export Formats**:
- CSV: Comma-separated values, plain text
- Excel: Formatted with headers bold, status color-coded (Green=Present, Orange=Late)

---

## 🔄 Data Flow: Complete User Journeys

### Journey 1: Lecturer Registration

```
1. Lecturer navigates to registration page
2. Submits: first_name, last_name, email, password, department_name
3. System validates input
4. Creates User (role=Lecturer, is_active=True auto-set)
5. Creates LecturerProfile (department_name stored)
6. Returns success response
7. Lecturer can immediately login with email+password
```

### Journey 2: Create Attendance Session

```
1. Lecturer logs in with email+password → JWT token issued
2. Lecturer creates session with:
   - course_id (must be assigned to them)
   - program_id (target program)
   - stream_id (optional, if program has streams)
   - GPS location (lecturer's current coordinates)
3. System validates:
   - Lecturer assigned to course ✓
   - Course belongs to program ✓
   - Stream belongs to program ✓
   - Student eligibility criteria ✓
4. Session saved with:
   - time_created = now
   - time_ended = now + 30 minutes (fixed)
5. Email Notification Context triggered:
   - Identifies eligible students (program + stream match + active)
   - Generates JWT token for each: {student_profile_id, session_id, exp}
   - Creates EmailNotification record (status=pending)
   - Queues background task
6. Background worker sends emails asynchronously
7. Returns session details to lecturer
```

### Journey 3: Student Marks Attendance

```
1. Student receives email with attendance link containing JWT token
2. Student clicks link (opens mobile-friendly attendance form)
3. Student scans QR code with phone camera
4. QR decoder extracts: student_id (e.g., "BCS/234344")
5. Student provides current GPS coordinates (latitude, longitude)
6. System validates in sequence:
   ✓ JWT token signature and expiry (30-min window)
   ✓ Scanned student_id matches token student
   ✓ Session exists and is active (within time_created to time_ended)
   ✓ Student eligible (program/stream match, active account)
   ✓ Distance calculation (Haversine formula)
   ✓ Duplicate check (hasn't already marked)
7. Attendance recorded with:
   - status = "present" (if within 30min AND within 30m)
   - status = "late" (if after 30min OR outside 30m)
   - is_within_radius = true/false (flag for auditing)
   - GPS coordinates stored (for audit trail)
8. Returns success: "Attendance marked as [Present/Late]"
```

### Journey 4: Generate Attendance Report

```
1. Lecturer (for own sessions) or Admin (for any) requests report
2. System authorizes user
3. Retrieves session metadata (course, program, stream, date, time)
4. Gets list of eligible students (by program/stream)
5. Queries attendance records for this session
6. Classifies each student:
   - Has attendance with status="present" → Present
   - Has attendance with status="late" OR no attendance → Late
7. Report created (view-only, no file yet)
8. User can:
   - View report online (table format)
   - Export to CSV (generates file, updates report metadata)
   - Export to Excel (generates formatted file, updates report metadata)
9. Reports stored indefinitely for audit trail
```

---

## 🔐 Security Features

### Three-Factor Attendance Verification
- **JWT Token**: Time-limited, signed, server-side secret
- **QR Code**: Physical possession verification
- **GPS Location**: Physical presence verification

### Email-Based Passwordless Authentication (Students)
- Students never set password
- Access via time-limited JWT tokens in email links
- Tokens tied to specific session and student

### Role-Based Access Control
- Admin: Full system access
- Lecturer: Limited to own courses/sessions/reports
- Student: Email link access only

### Audit Trail
- All attendance marked with server timestamp (not client)
- GPS coordinates stored for location audit
- Complete action history via database records

---

## 📊 Data Models Overview

### Key Relationships

```
User
├── LecturerProfile (1 lecturer per user)
│   └── Courses (many-to-one via lecturer_id)
│       └── Sessions (many-to-one via course_id)
│           ├── EmailNotifications (many-to-one via session_id)
│           └── Attendance (many-to-one via session_id)
└── StudentProfile (1 student per user)
    ├── Program (many-to-one via program_id)
    │   ├── Streams (one-to-many via program_id)
    │   └── Courses (one-to-many via program_id)
    └── Attendance (many-to-one via student_profile_id)

Program
├── has_streams: Boolean flag
├── Streams (only if has_streams=True)
└── Courses

Session
├── program_id → Program
├── stream_id → Stream (nullable)
├── course_id → Course
├── lecturer_id → LecturerProfile
├── EmailNotifications
└── Attendance records
```

### Nullable Fields (by Design)

| Entity | Field | Reason |
|--------|-------|--------|
| User | `password` | Students use passwordless JWT auth |
| StudentProfile | `stream_id` | Programs may not have streams |
| Course | `lecturer_id` | Can be unassigned initially |
| Session | `stream_id` | Can target entire program |
| EmailNotification | `sent_at` | NULL until email successfully sent |
| Report | `file_path`, `file_type` | NULL if report not exported |

---

## 🚀 Constraints & Business Rules Summary

### Time Windows
- **Session Duration**: Fixed 30 minutes (non-configurable)
- **Token Expiry**: 30 minutes from session creation
- **Attendance Marking Window**: 30 minutes from session start time
- **Present Classification**: Must mark within first 30 minutes AND within 30m radius
- **Late Classification**: Marked after 30min OR outside 30m (still recorded)

### Format Validations
- **Student ID**: `^[A-Z]{3}/[0-9]{6}$` (e.g., `BCS/234344`)
- **Program Code**: `^[A-Z]{3}$` (e.g., "BCS")
- **Course Code**: `^[A-Z]{3}[0-9]{3}$` (e.g., "BCS201")
- **QR Code Data**: Must equal student ID (database CHECK constraint)

### GPS Coordinates
- **Latitude**: -90 to +90 degrees
- **Longitude**: -180 to +180 degrees
- **Radius Validation**: Haversine formula with 30-meter threshold
- **Earth Radius Constant**: 6,371,000 meters

### Cascading Deletes
- Deleting User → Deletes LecturerProfile or StudentProfile
- Deleting Program → Deletes Streams and Courses
- Deleting Session → Deletes EmailNotifications and Attendance
- Lecturer deletion → Course `lecturer_id` set to NULL (course preserved)

---

## �️ Implementation Recommendations

### Start With These Contexts (In Order)

1. **User Management** (Few dependencies)
   - Foundation for all other contexts
   - Defines roles and access control

2. **Academic Structure** (Depends on User Management)
   - Define organizational hierarchy
   - Validate lecturer assignments

3. **Session Management** (Depends on User Management + Academic Structure)
   - Core lecturer functionality
   - Triggers email notifications

4. **Email Notifications** (Depends on Session Management)
   - Background task processing
   - Token generation

5. **Attendance Recording** (Depends on all above)
   - Student-facing functionality
   - Location validation

6. **Reporting** (Depends on all above)
   - Analysis and export
   - Access control checks

### For Each Context, Follow This Order

1. **Models** - Define data structure and constraints
2. **Repositories** - Implement data access layer
3. **Services** - Implement business logic and validation
4. **Handlers** - Orchestrate application flow
5. **Serializers & Validators** - Input/output handling
6. **Views** - HTTP endpoints and API
7. **Permissions** - Role-based access control
8. **Tests** - Unit and integration tests

---

## 🔍 Key Design Patterns

### Bounded Contexts (DDD)
- Clear boundaries between domains
- Explicit dependencies between contexts
- Each context owns its data and business logic

### Repository Pattern
- Data access abstraction
- Testability via mock repositories
- Consistent query interface

### Service Layer
- Business logic encapsulation
- Transaction management
- Validation coordination

### Command/Query Handler Pattern
- Application layer orchestration
- Use case separation
- DTOs for data transfer

### Three-Factor Verification
- Multi-layer security (token + QR + GPS)
- No single point of failure
- Audit trail for all attempts

---

## 🎓 Technology Stack

- **Framework**: Django (Python web framework)
- **Database**: PostgreSQL (relational database)
- **Authentication**: JWT (JSON Web Tokens)
- **Task Queue**: Celery (background job processing)
- **Email**: SMTP (Simple Mail Transfer Protocol)
- **Geolocation**: Haversine formula (distance calculation)
- **Export**: CSV and Excel formats

---

## �📁 Detailed Documentation Structure

```
proj_docs/
├── docs/
│   ├── shared/                  # Shared documentation (system flows, overview, roles, etc.)
│   │   ├── BOUNDED_CONTEXTS_OVERVIEW.md
│   │   ├── COMPLETE_SYSTEM_FLOWS.md
│   │   ├── api_guide.md
│   │   ├── attendance_management_doc.md
│   │   ├── entities_relationships.md
│   │   ├── models_guide.md
│   │   ├── project_overview.md
│   │   ├── repositories_guide.md
│   │   ├── services_guide.md
│   │   ├── user_roles.md
│   │   └── workflow.md
│   └── contexts/               # One folder per bounded context
│       ├── academic-structure/
│       │   ├── README.md
│       │   ├── academic_structure app structure.ini
│       │   ├── api_guide.md
│       │   ├── models_guide.md
│       │   ├── repositories_guide.md
│       │   ├── services_guide.md
│       │   └── testing_guide.md
│       ├── attendance-recording/
│       │   ├── README.md
│       │   ├── attendance_recording app structure.ini
│       │   ├── api_guide.md
│       │   ├── models_guide.md
│       │   ├── repositories_guide.md
│       │   ├── services_guide.md
│       │   └── testing_guide.md
│       ├── email-notifications/
│       │   ├── README.md
│       │   ├── email_notification app struccture.ini
│       │   ├── api_guide.md
│       │   ├── models_guide.md
│       │   ├── repositories_guide.md
│       │   ├── services_guide.md
│       │   └── testing_guide.md
│       ├── reporting/
│       │   ├── README.md
│       │   ├── reporting app structure.ini
│       │   ├── api_guide.md
│       │   ├── models_guide.md
│       │   ├── repositories_guide.md
│       │   ├── services_guide.md
│       │   └── testing_guide.md
│       ├── session-management/
│       │   ├── README.md
│       │   ├── session_management app structure
│       │   ├── api_guide.md
│       │   ├── models_guide.md
│       │   ├── repositories_guide.md
│       │   ├── services_guide.md
│       │   └── testing_guide.md
│       └── user-management/
│           ├── README.md
│           ├── user-management app structure
│           ├── api_guide.md
│           ├── models_guide.md
│           ├── repositories_guide.md
│           ├── services_guide.md
│           └── testing_guide.md
├── requirements.txt
├── README.md
```

## 📚 Documentation Guide



### Getting Started

1. **Start with Project Overview**
   - Read `docs/shared/project_overview.md` to understand the system purpose
   - Review `docs/shared/workflow.md` for general system flow
   - Check `docs/shared/user_roles.md` for role definitions

2. **Explore Bounded Contexts & Blueprints**
   - Go to `docs/contexts/` for a summary of all DDD bounded contexts
   - Each context folder contains:
     - An app structure file (folder/file tree with descriptions)
     - Implementation guides (models, repositories, services, API, testing)
   - Use these as blueprints for implementation and onboarding

3. **Understand the Domain**
   - Read `docs/shared/attendance_management_doc.md` for the bounded context
   - Review `docs/shared/entities_relationships.md` for entity relationships

4. **Learn the Architecture**
   - Read `docs/shared/COMPLETE_SYSTEM_FLOWS.md` for end-to-end flows
   - Study other shared guides in `docs/shared/`

### Documentation by Concern

#### 🏛️ **Architecture & Design**
- **System Flows**: `docs/COMPLETE_SYSTEM_FLOWS.md`
  - Complete trace of every use case through all layers
  - Request/response examples
  - Error handling flows
  
- **Domain Model**: `design/domain_model.md`
  - Aggregates, entities, and value objects
  - Domain services and repositories
  - Business rules and invariants

- **ERD**: `design/erd.md`
  - Database schema design
  - Entity relationships
  - Constraints and indexes

#### 💻 **Implementation Guides**

- **Application Layer**: `docs/implementation/APPLICATION_LAYER_GUIDE.md`
  - Commands and handlers
  - DTOs (Data Transfer Objects)
  - Event bus and subscribers
  - Use case orchestration

- **Domain Layer**: `docs/implementation/DOMAIN_LAYER_GUIDE.md`
  - Domain entities implementation
  - Value objects (Email, Location, PasswordHash)
  - Domain services (LocationValidator, AttendancePolicy)
  - Repository interfaces

- **Infrastructure Layer**: `docs/implementation/INFRASTRUCTURE_LAYER_GUIDE.md`
  - JWT token provider
  - Password hashing service
  - Email service and background tasks
  - Repository implementations (Django ORM)
  - Dependency injection container

- **Technical Implementation**: `docs/implementation/TECHNICAL_IMPLEMENTATION.md`
  - Haversine distance calculation
  - QR code handling
  - Email system setup
  - Token security
  - Web app specifics

#### 🔌 **API & Integration**

- **API Specification**: `design/api_spec.md`
  - Endpoint definitions
  - Request/response formats
  - Authentication requirements
  - Error responses

- **Sequence & Token Flow**: `design/sequence_and_token_flow.md`
  - Token lifecycle
  - Sequence diagrams
  - Email notification flow
  - Token validation process

- **Security & Deployment**: `design/security_and_deployment.md`
  - Security best practices
  - Token management
  - Deployment guidelines
  - Monitoring and logging

## 🎯 Documentation by Role

### **For Developers**

**Starting Development:**
1. `docs/project_overview.md` - Understand what you're building
2. `docs/implementation/INSTRUCTIONS_DDD_PY.md` - Setup and DDD guidelines
3. `docs/implementation/DOMAIN_LAYER_GUIDE.md` - Start with domain entities
4. `docs/implementation/APPLICATION_LAYER_GUIDE.md` - Build use cases
5. `docs/implementation/INFRASTRUCTURE_LAYER_GUIDE.md` - Implement services

**During Development:**
- Reference `docs/COMPLETE_SYSTEM_FLOWS.md` for understanding data flow
- Use `design/api_spec.md` for API contracts
- Check `docs/implementation/TECHNICAL_IMPLEMENTATION.md` for algorithms

### **For Project Managers**

**Understanding Scope:**
1. `docs/project_overview.md` - Project goals
2. `docs/workflow.md` - System workflow
3. `docs/attendance_management_doc.md` - Features and requirements

**Monitoring Progress:**
- `docs/COMPLETE_SYSTEM_FLOWS.md` - Track feature implementation
- `design/api_spec.md` - API readiness checklist

### **For System Architects**

**Architecture Review:**
1. `docs/COMPLETE_SYSTEM_FLOWS.md` - System architecture layers
2. `design/domain_model.md` - Domain design
3. `design/erd.md` - Data model
4. `design/security_and_deployment.md` - Infrastructure planning

**Design Patterns:**
- All files in `docs/implementation/` - Layer-specific patterns
- `design/sequence_and_token_flow.md` - Interaction patterns

### **For QA/Testers**

**Test Planning:**
1. `docs/workflow.md` - User workflows to test
2. `docs/COMPLETE_SYSTEM_FLOWS.md` - Expected system behavior
3. `design/api_spec.md` - API test cases
4. `docs/implementation/TECHNICAL_IMPLEMENTATION.md` - Edge cases (location, tokens)

## 🔄 Documentation Maintenance

### Structure Principles

This documentation follows the structure established in the DETAILS project:

1. **Top-level docs/** - High-level documentation and complete system flows
2. **docs/implementation/** - Layer-specific implementation guides
3. **design/** - Design specifications and API contracts
4. **src/** - Reference code implementations
5. **examples/** - Working code examples
6. **tests/** - Test examples

### When to Update

- **Domain changes**: Update `design/domain_model.md` and `docs/implementation/DOMAIN_LAYER_GUIDE.md`
- **API changes**: Update `design/api_spec.md` and corresponding flow documents
- **New features**: Add to `docs/COMPLETE_SYSTEM_FLOWS.md` and relevant guides
- **Infrastructure changes**: Update `docs/implementation/INFRASTRUCTURE_LAYER_GUIDE.md`

## 🚀 Quick Reference

### Most Used Documents

| Task | Document |
|------|----------|
| Understanding the system | `docs/project_overview.md` |
| Implementing a feature | `docs/COMPLETE_SYSTEM_FLOWS.md` |
| Working with domain entities | `docs/implementation/DOMAIN_LAYER_GUIDE.md` |
| Building API endpoints | `design/api_spec.md` |
| Setting up JWT tokens | `docs/implementation/INFRASTRUCTURE_LAYER_GUIDE.md` |
| Calculating distances | `docs/implementation/TECHNICAL_IMPLEMENTATION.md` |
| Understanding database | `design/erd.md` |

### Code Examples

- **JWT Token Generation**: `src/infrastructure/jwt_provider.py`
- **Email Service**: `src/infrastructure/emailer.py`
- **Background Tasks**: `src/infrastructure/email_tasks.py`
- **Complete Example**: `examples/token_email_example.py`

## 📝 Contributing to Documentation

When adding new documentation:

1. **Choose the right location**:
   - High-level concepts → `docs/`
   - Implementation details → `docs/implementation/`
   - Design specs → `design/`
   - Code examples → `src/` or `examples/`

2. **Follow naming conventions**:
   - Use UPPERCASE for major guides (e.g., `DOMAIN_LAYER_GUIDE.md`)
   - Use snake_case for specific docs (e.g., `attendance_management_doc.md`)
   - Be descriptive in file names

3. **Include in this README**:
   - Add new documents to the structure diagram
   - Add to relevant "Documentation by Concern" section
   - Update quick reference if applicable

## 🔗 Related Resources

- **DETAILS Project** (reference): `/home/chussey/Desktop/DETAILS/docs/`
- **Main Codebase**: `/home/chussey/Desktop/DETAILS/apps/user_management/`

---

**Last Updated**: October 14, 2025  
**Restructured**: Based on DETAILS project documentation patterns
