# API Guide - Complete System API Reference

This document provides a comprehensive overview of all API endpoints across the QR Code-Based Attendance Management System, organized by bounded context. Each context has its own detailed API guide; this serves as a central reference and navigation hub.

---

## System-Wide API Conventions

### Authentication
- **JWT Bearer Tokens**: Most endpoints use standard JWT authentication
  - Header format: `Authorization: Bearer <token>`
  - Token contains user_id, role, and expiration
- **Token-Based (Body)**: Attendance recording uses tokens in request body (not header)
  - Used for email link-based attendance marking
  - Token in body: `{ "token": "eyJhbGc..." }`

### Authorization Roles
- **Admin**: Full CRUD access across all contexts
- **Lecturer**: Read access + create/manage own sessions
- **Student**: Limited access (attendance marking only)

### Standard Response Formats

**Success Response**:
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

**Error Response**:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { ... }
  }
}
```

### HTTP Status Codes
- `200` - OK (successful query)
- `201` - Created (successful resource creation)
- `204` - No Content (successful deletion)
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource doesn't exist)
- `409` - Conflict (duplicate/constraint violation)
- `410` - Gone (expired/ended resource)
- `425` - Too Early (resource not ready)
- `500` - Internal Server Error

---

## API by Bounded Context

### 1. User Management Context

**Purpose**: User authentication, profile management (students, lecturers, admins)

**Base Path**: `/api/users/`

**Key Endpoints**:
- `POST /api/users/register` - Register new user (student/lecturer)
- `POST /api/users/login` - Authenticate and receive JWT token
- `GET /api/users/{user_id}` - Get user details
- `PUT /api/users/{user_id}` - Update user information
- `DELETE /api/users/{user_id}` - Deactivate user account
- `GET /api/users/{user_id}/student-profile` - Get student profile
- `PUT /api/users/{user_id}/student-profile` - Update student profile
- `GET /api/users/{user_id}/lecturer-profile` - Get lecturer profile
- `PUT /api/users/{user_id}/lecturer-profile` - Update lecturer profile

**Authentication**: JWT Bearer (except register/login)

**Key Features**:
- JWT-based authentication for all endpoints
- Separate profile management for students and lecturers
- Role-based authorization (admin, lecturer, student)
- Password hashing and validation

**For Details**: See `/docs/contexts/user-management/api_guide.md`

---

### 2. Academic Structure Context

**Purpose**: Manage programs, courses, streams, and cohorts

**Base Path**: `/api/academic-structure/v1/`

**Key Endpoints**:

**Programs**:
- `GET /programs` - List programs (filterable, paginated)
- `POST /programs` - Create program (admin only)
- `GET /programs/{program_id}` - Get program by ID
- `GET /programs/by-code/{program_code}` - Get program by code
- `PATCH /programs/{program_id}` - Update program
- `DELETE /programs/{program_id}` - Delete program (safe delete)

**Streams**:
- `GET /programs/{program_id}/streams` - List program streams
- `POST /programs/{program_id}/streams` - Create stream (admin only)
- `GET /streams/{stream_id}` - Get stream by ID
- `PATCH /streams/{stream_id}` - Update stream
- `DELETE /streams/{stream_id}` - Delete stream (safe delete)

**Courses**:
- `GET /courses` - List courses (filterable, paginated)
- `POST /courses` - Create course (admin only)
- `GET /courses/{course_id}` - Get course by ID
- `GET /courses/by-code/{course_code}` - Get course by code
- `PATCH /courses/{course_id}` - Update course
- `POST /courses/{course_id}/assign-lecturer` - Assign lecturer to course
- `POST /courses/{course_id}/unassign-lecturer` - Remove lecturer assignment
- `DELETE /courses/{course_id}` - Delete course (safe delete)

**Authentication**: JWT Bearer (lecturer read-only, admin full access)

**Key Features**:
- Pagination and filtering support
- Safe delete (prevents deletion if resources in use)
- Lecturer assignment to courses
- Stream support (optional per program)

**For Details**: See `/docs/contexts/academic-structure/api_guide.md`

---

### 3. Session Management Context

**Purpose**: Lecturers create and manage attendance sessions

**Base Path**: `/api/session-management/v1/`

**Key Endpoints**:
- `POST /sessions` - Create new session (lecturer only)
- `GET /sessions` - List sessions (filterable by course, program, stream, time)
- `GET /sessions/{session_id}` - Get session details
- `POST /sessions/{session_id}/end-now` - End session early
- `GET /admin/sessions` - List all sessions (admin only)

**Authentication**: JWT Bearer (lecturer role required for creation)

**Key Features**:
- Lecturer-only session creation
- Geolocation validation (latitude/longitude)
- Time window enforcement (10m-24h duration)
- No overlapping sessions for lecturer
- Stream targeting (optional, must match program)
- Automatic email notification trigger on session creation

**Request Example**:
```json
{
  "program_id": 1,
  "course_id": 301,
  "stream_id": 25,
  "time_created": "2025-10-25T08:00:00Z",
  "time_ended": "2025-10-25T10:00:00Z",
  "latitude": "-1.28333412",
  "longitude": "36.81666588",
  "location_description": "Room A101"
}
```

**For Details**: See `/docs/contexts/session-management/api_guide.md`

---

### 4. Attendance Recording Context

**Purpose**: Students mark attendance using token-based links

**Base Path**: `/api/v1/attendance/`

**Key Endpoint**:
- `POST /api/v1/attendance/mark` - Mark attendance (token-based, NOT JWT Bearer)

**Authentication**: Token in request body (from email link)

**Request Format**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "scanned_student_id": "BCS/234344",
  "latitude": "-1.28334000",
  "longitude": "36.81667000"
}
```

**Key Features**:
- **Three-factor verification**: Token + QR code + GPS location
- **Token-based auth**: Token in body (not Authorization header)
- **Idempotent**: Returns 409 Conflict if already marked
- **Immutable records**: No update or delete endpoints
- **Status assignment**: "present" (within 30m radius) or "late" (outside radius)
- **Comprehensive error codes**: 14 error scenarios covered
- **Fraud detection**: QR code mismatch logged

**Response (201 Created)**:
```json
{
  "success": true,
  "data": {
    "attendance_id": 501,
    "student_profile_id": 123,
    "session_id": 456,
    "status": "present",
    "is_within_radius": true,
    "time_recorded": "2025-10-25T08:05:23.456Z"
  }
}
```

**Error Codes**:
- `INVALID_REQUEST` (400) - Validation errors
- `QR_CODE_MISMATCH` (403) - Fraud attempt
- `DUPLICATE_ATTENDANCE` (409) - Already marked
- `TOKEN_EXPIRED` (410) - Link expired
- `SESSION_ENDED` (410) - Session finished
- `SESSION_NOT_STARTED` (425) - Too early

**For Details**: See `/docs/contexts/attendance-recording/api_guide.md`

---

### 5. Email Notifications Context

**Purpose**: Generate and send attendance notification emails with JWT tokens

**Base Path**: `/api/email-notifications/v1/`

**Key Endpoints**:
- `POST /internal/sessions/{session_id}/notifications` - Generate notifications (internal only)
- `POST /admin/notifications/retry` - Retry failed emails (admin only)
- `GET /sessions/{session_id}/notifications` - View notification status (lecturer/admin)
- `GET /admin/notifications/statistics` - System-wide statistics (admin only)

**Authentication**: 
- Internal service token (for generation)
- JWT Bearer (for admin/monitoring)

**Key Features**:
- **Mostly internal API**: Triggered by session creation
- **Async workflow**: Notifications queued (pending), sent by background worker
- **Admin retry support**: Recover from SMTP failures
- **Monitoring**: View delivery status per session
- **No student access**: Students receive emails, don't manage them

**Internal Call Example** (Session Management → Email Notifications):
```json
POST /internal/sessions/123/notifications
Response (201):
{
  "status": "success",
  "data": {
    "session_id": 123,
    "notifications_created": 45,
    "eligible_students": 45
  }
}
```

**For Details**: See `/docs/contexts/email-notifications/api_guide.md`

---

### 6. Reporting Context

**Purpose**: Generate, export, and download attendance reports

**Base Path**: `/api/v1/`

**Key Endpoints**:
- `POST /api/v1/sessions/{session_id}/report/` - Generate report
- `GET /api/v1/reports/{report_id}/` - View report
- `POST /api/v1/reports/{report_id}/export/` - Export to CSV/Excel
- `GET /api/v1/reports/{report_id}/download/` - Download exported file
- `GET /api/v1/reports/` - List all reports (admin only)

**Authentication**: JWT Bearer (lecturer/admin)

**Authorization**:
- Lecturer: Can generate/view/export reports for own sessions
- Admin: Can access all reports

**Key Features**:
- **Report generation**: Creates Report record with statistics
- **Export formats**: CSV or Excel
- **Immutability**: 409 Conflict on re-export (prevent overwrites)
- **File download**: Proper Content-Disposition headers
- **Statistics included**: Total students, present/late/absent counts, percentages
- **Student list**: Complete attendance details with GPS coordinates

**Generate Report Response (201)**:
```json
{
  "success": true,
  "data": {
    "report_id": 101,
    "session": { ... },
    "statistics": {
      "total_students": 50,
      "present_count": 35,
      "present_percentage": 70.0,
      "late_count": 8,
      "absent_count": 7
    },
    "students": [ ... ],
    "export_status": "not_exported"
  }
}
```

**Export Request**:
```json
{
  "file_type": "csv"  // or "excel"
}
```

**For Details**: See `/docs/contexts/reporting/api_guide.md`

---

## API Integration Flow

### Complete Attendance Workflow

1. **Lecturer Creates Session** (Session Management)
   ```
   POST /api/session-management/v1/sessions
   → 201 Created with session_id
   ```

2. **Email Notifications Generated** (Internal Call)
   ```
   POST /internal/sessions/{session_id}/notifications
   → 201 Created (45 notifications queued)
   ```

3. **Student Receives Email** (Background Worker)
   ```
   Email contains link: https://app.edu/attendance?token=eyJhbGc...
   ```

4. **Student Marks Attendance** (Attendance Recording)
   ```
   POST /api/v1/attendance/mark
   Body: { token, scanned_student_id, latitude, longitude }
   → 201 Created (attendance recorded)
   ```

5. **Lecturer Generates Report** (Reporting)
   ```
   POST /api/v1/sessions/{session_id}/report/
   → 201 Created (report with statistics)
   ```

6. **Lecturer Exports Report** (Reporting)
   ```
   POST /api/v1/reports/{report_id}/export/
   Body: { "file_type": "csv" }
   → 200 OK (file generated)
   ```

7. **Lecturer Downloads File** (Reporting)
   ```
   GET /api/v1/reports/{report_id}/download/
   → 200 OK (CSV file download)
   ```

---

## Security Considerations

### Authentication Methods
1. **JWT Bearer** (Standard): User Management, Academic Structure, Session Management, Reporting
2. **Token in Body** (Special): Attendance Recording (email link-based)
3. **Service Token** (Internal): Email Notifications generation

### Authorization Patterns
- **Admin-only**: Program/course/stream creation, notification retry, all reports
- **Lecturer-only**: Session creation, own session reports
- **Student-only**: Attendance marking (via token)
- **Public**: User registration, login

### Rate Limiting Recommendations
- Session creation: 10 requests/minute per lecturer
- Attendance marking: 3 requests/minute per IP
- Report generation: 20 requests/minute per user
- Notification retry: 5 requests/minute per admin

### HTTPS Required
- Tokens transmitted in body/header (sensitive)
- GPS coordinates (location privacy)
- All endpoints must use HTTPS in production

---

## Error Handling Patterns

### Validation Errors (400)
```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Validation failed",
    "details": {
      "field_name": ["error description"]
    }
  }
}
```

### Authorization Errors (403)
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "You do not have permission to perform this action",
    "details": { ... }
  }
}
```

### Resource Not Found (404)
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Resource with id 999 not found",
    "details": { "resource_id": 999 }
  }
}
```

### Conflict Errors (409)
```json
{
  "success": false,
  "error": {
    "code": "DUPLICATE_RESOURCE",
    "message": "Resource already exists",
    "details": { ... }
  }
}
```

---

## Context-Specific API Documentation

For detailed endpoint specifications, request/response examples, error codes, and implementation details, refer to the API guide in each context folder:

- **User Management**: `/docs/contexts/user-management/api_guide.md`
- **Academic Structure**: `/docs/contexts/academic-structure/api_guide.md`
- **Session Management**: `/docs/contexts/session-management/api_guide.md`
- **Attendance Recording**: `/docs/contexts/attendance-recording/api_guide.md`
- **Email Notifications**: `/docs/contexts/email-notifications/api_guide.md`
- **Reporting**: `/docs/contexts/reporting/api_guide.md`

---

## Quick Reference

### Most Used Endpoints

| Task | Endpoint | Context |
|------|----------|---------|
| User login | `POST /api/users/login` | User Management |
| Create session | `POST /api/session-management/v1/sessions` | Session Management |
| Mark attendance | `POST /api/v1/attendance/mark` | Attendance Recording |
| Generate report | `POST /api/v1/sessions/{id}/report/` | Reporting |
| Export report | `POST /api/v1/reports/{id}/export/` | Reporting |
| List programs | `GET /api/academic-structure/v1/programs` | Academic Structure |

---

**Status**: ✅ Complete system-wide API reference  
**Last Updated**: October 21, 2025