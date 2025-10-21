# api_guide.md

Brief: Complete API specification for Attendance Recording. Public POST endpoint for marking attendance using token-based authentication (NOT JWT Bearer). Three-factor verification workflow with detailed error responses, immutability rules, and duplicate prevention.

---

## API Layer Purpose

**Why API Matters**:
- **Public endpoint**: Students access via email link (no JWT Bearer header)
- **Token-based auth**: Token in request body (from email link query param)
- **Three-factor verification**: Token + QR + GPS in single request
- **Idempotent duplicate handling**: 409 Conflict if already marked
- **Immutable records**: No PUT/PATCH/DELETE endpoints

**Priority: CRITICAL** - Entry point for attendance marking

---

# AUTHENTICATION MODEL

## Token-Based (Not JWT Bearer)

**How It Works**:
1. Student receives email with link: `https://app.edu/attendance?token=eyJhbGc...`
2. Frontend extracts token from URL query parameter
3. Frontend sends token in request body (not Authorization header)
4. Backend validates token using TokenValidator service

**Why Not JWT Bearer**:
- Email links can't set Authorization headers
- Students click link from any device (mobile, desktop)
- Token in body allows simple form submission
- No need for session management

**Security Considerations**:
- Token expires after 30-60 minutes (set by Email Notification context)
- Single-use encouraged (duplicate prevention)
- HTTPS required (token in transit)

**Priority: CRITICAL** - Non-standard auth pattern

---

# ENDPOINTS

## POST /api/v1/attendance/mark

**Purpose**: Mark attendance for a session with three-factor verification

**Authentication**: Token-based (token in request body)

**Method**: POST (create new attendance record)

**Priority: CRITICAL** - Only public endpoint

---

### Request Format

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdHVkZW50X3Byb2ZpbGVfaWQiOjEyMywic2Vzc2lvbl9pZCI6NDU2LCJpYXQiOjE3MjkzMzkyMDAsImV4cCI6MTcyOTM0MjgwMH0.signature",
  "scanned_student_id": "BCS/234344",
  "latitude": "-1.28334000",
  "longitude": "36.81667000"
}
```

**Field Specifications**:

| Field | Type | Required | Validation | Example |
|-------|------|----------|------------|---------|
| `token` | string | ✅ Yes | JWT format (3 parts) | `eyJhbGc...` |
| `scanned_student_id` | string | ✅ Yes | Regex: `^[A-Z]{3}/[0-9]{6}$` | `BCS/234344` |
| `latitude` | string | ✅ Yes | Decimal -90 to 90, 8 decimals | `"-1.28334000"` |
| `longitude` | string | ✅ Yes | Decimal -180 to 180, 8 decimals | `"36.81667000"` |

**Why Strings for Coordinates**: 
- Prevent floating-point precision loss
- Parsed to Decimal on backend
- Consistent with database Decimal(10,8) and Decimal(11,8)

**Validation Rules**:
- All fields required (400 if missing)
- Token must be valid JWT format
- QR code must match regex pattern
- Coordinates must be valid ranges
- Coordinates cannot be (0, 0) or NULL

---

### Success Response (201 Created)

**Status Code**: 201 Created

**Response Body**:
```json
{
  "success": true,
  "data": {
    "attendance_id": 501,
    "student_profile_id": 123,
    "session_id": 456,
    "status": "present",
    "is_within_radius": true,
    "time_recorded": "2025-10-25T08:05:23.456Z",
    "latitude": "-1.28334000",
    "longitude": "36.81667000"
  },
  "message": "Attendance marked successfully"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Always `true` for 2xx responses |
| `attendance_id` | integer | Primary key of created record |
| `status` | string | `"present"` or `"late"` |
| `is_within_radius` | boolean | True if within 30m, false otherwise |
| `time_recorded` | ISO 8601 | UTC timestamp of record creation |

**Why 201 Created**: New resource created (not 200 OK)

---

### Error Responses

**Priority: CRITICAL** - Clear error messages for user experience

#### 400 Bad Request - Validation Errors

**Scenarios**:
- Missing required field
- Invalid JWT format
- Invalid QR code format
- Invalid GPS coordinates
- Invalid signature (tampered token)

**Example Response**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid QR code format. Please scan your student ID card.",
    "details": {
      "field": "scanned_student_id",
      "value": "bcs/234344",
      "expected_format": "^[A-Z]{3}/[0-9]{6}$"
    }
  }
}
```

**User-Facing Messages**:
- Missing field: "All fields are required"
- Invalid token: "Invalid attendance link"
- Invalid QR: "Invalid QR code format. Please scan your student ID card."
- Invalid coordinates: "Invalid GPS coordinates. Please enable location services."

---

#### 403 Forbidden - Authorization Errors

**Scenarios**:
- QR code doesn't match token student (fraud attempt)
- Student account inactive
- Program mismatch (student not in session's program)
- Stream mismatch (session targets different stream)

**Example Response**:
```json
{
  "success": false,
  "error": {
    "code": "QR_CODE_MISMATCH",
    "message": "This QR code does not match your attendance link. Please use your own student ID.",
    "details": {
      "scanned_student_id": "MIT/123456",
      "expected_student_id": "BCS/234344"
    }
  }
}
```

**Why 403 (Not 401)**:
- Request is authenticated (token valid)
- Authorization failed (not allowed to access resource)

**Security Note**: Log QR code mismatch attempts for fraud investigation

---

#### 404 Not Found - Resource Errors

**Scenarios**:
- Session doesn't exist
- Student profile doesn't exist

**Example Response**:
```json
{
  "success": false,
  "error": {
    "code": "SESSION_NOT_FOUND",
    "message": "Session not found. Please contact your lecturer.",
    "details": {
      "session_id": 456
    }
  }
}
```

**User-Facing Messages**:
- Session not found: "Session not found. Please contact your lecturer."
- Student not found: "Student profile not found. Please contact administration."

---

#### 409 Conflict - Duplicate Attendance

**Scenario**: Student already marked attendance for this session

**Example Response**:
```json
{
  "success": false,
  "error": {
    "code": "DUPLICATE_ATTENDANCE",
    "message": "You have already marked attendance for this session.",
    "details": {
      "existing_attendance_id": 500,
      "time_recorded": "2025-10-25T08:03:15.123Z",
      "status": "present"
    }
  }
}
```

**Why Important**:
- Prevents double submission
- Enforces unique constraint
- Shows existing record details (reassurance)

**User Experience**: "You have already marked attendance for this session at 8:03 AM."

**Priority: HIGH** - Prevents duplicate records

---

#### 410 Gone - Expired/Ended Resources

**Scenarios**:
- Token expired
- Session has ended

**Example Response (Expired Token)**:
```json
{
  "success": false,
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "Your attendance link has expired. Please contact your lecturer for a new link.",
    "details": {
      "expired_at": "2025-10-25T09:00:00.000Z",
      "current_time": "2025-10-25T09:15:00.000Z"
    }
  }
}
```

**Example Response (Session Ended)**:
```json
{
  "success": false,
  "error": {
    "code": "SESSION_ENDED",
    "message": "This session has ended. Attendance window is closed.",
    "details": {
      "session_ended_at": "2025-10-25T10:00:00.000Z",
      "current_time": "2025-10-25T10:30:00.000Z"
    }
  }
}
```

**Why 410 (Not 400)**:
- Resource existed but is no longer available
- Different from 404 (never existed)
- Indicates time-based expiry

---

#### 425 Too Early - Session Not Started

**Scenario**: Student tries to mark attendance before session starts

**Example Response**:
```json
{
  "success": false,
  "error": {
    "code": "SESSION_NOT_STARTED",
    "message": "This session has not started yet. Please wait until 8:00 AM.",
    "details": {
      "session_starts_at": "2025-10-25T08:00:00.000Z",
      "current_time": "2025-10-25T07:45:00.000Z",
      "minutes_until_start": 15
    }
  }
}
```

**Why 425 Too Early**: RFC 8470 - request before resource is ready

**User Experience**: Show countdown timer until session starts

---

#### 500 Internal Server Error - System Errors

**Scenarios**:
- Database connection failure
- SMTP service down (for logging)
- Unexpected exceptions

**Example Response**:
```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred. Please try again or contact support.",
    "details": {
      "request_id": "req_abc123xyz"
    }
  }
}
```

**Priority: HIGH** - Never expose internal details to users

**Logging**: Log full stack trace server-side, return generic message to user

---

# ERROR CODE REFERENCE

| Error Code | HTTP Status | Scenario |
|------------|-------------|----------|
| `INVALID_REQUEST` | 400 | Missing/invalid field |
| `INVALID_TOKEN` | 400 | Malformed JWT |
| `INVALID_QR_FORMAT` | 400 | QR code format invalid |
| `INVALID_COORDINATES` | 400 | GPS out of range |
| `QR_CODE_MISMATCH` | 403 | Fraud attempt (QR doesn't match token) |
| `INACTIVE_STUDENT` | 403 | Student account disabled |
| `PROGRAM_MISMATCH` | 403 | Student not in session's program |
| `STREAM_MISMATCH` | 403 | Session targets different stream |
| `SESSION_NOT_FOUND` | 404 | Session doesn't exist |
| `STUDENT_NOT_FOUND` | 404 | Student profile doesn't exist |
| `DUPLICATE_ATTENDANCE` | 409 | Already marked attendance |
| `TOKEN_EXPIRED` | 410 | JWT past expiry time |
| `SESSION_ENDED` | 410 | Session has finished |
| `SESSION_NOT_STARTED` | 425 | Session hasn't begun yet |
| `INTERNAL_ERROR` | 500 | System error |

**Priority: CRITICAL** - Consistent error codes for frontend handling

---

# REQUEST/RESPONSE FLOW

## Complete Workflow

```
1. Student receives email with token link
   ↓
2. Student clicks link → Frontend extracts token
   ↓
3. Frontend prompts for QR code scan
   ↓
4. Frontend requests GPS location
   ↓
5. Frontend sends POST request with all data
   ↓
6. Handler calls AttendanceService.mark_attendance()
   ↓
7. Service validates:
   - Token (JWT) ✓
   - QR code match ✓
   - Session active ✓
   - Student eligible ✓
   - No duplicate ✓
   - GPS valid ✓
   - Calculate distance
   ↓
8. Service creates attendance record
   ↓
9. Handler returns 201 Created with details
   ↓
10. Frontend shows success message
```

**Priority: HIGH** - Understand complete user journey

---

# HANDLER LAYER STRUCTURE

## File Organization

**Priority: MEDIUM** - Maintainability

```
attendance_recording/
├── handlers/
│   ├── __init__.py
│   └── mark_attendance_handler.py       # Single handler for POST endpoint
├── services/
│   └── attendance_service.py            # Handler delegates to service
├── views.py                              # Django view wrapper (thin layer)
├── urls.py                               # URL routing
└── serializers.py                        # Request/response validation
```

**Why Handler Layer**:
- Separates HTTP concerns from business logic
- Service remains technology-agnostic
- Handler maps service exceptions to HTTP responses
- Validates request format before calling service

---

## Handler Responsibilities

**MarkAttendanceHandler** (`handlers/mark_attendance_handler.py`):

1. **Request Validation** → Validate JSON structure using serializer
2. **Service Invocation** → Call `AttendanceService.mark_attendance()`
3. **Exception Mapping** → Convert domain exceptions to HTTP responses
4. **Response Formatting** → Wrap service response in API envelope
5. **Logging** → Log fraud attempts, errors, success

**Why Thin Layer**: Handler is just glue code, service has all business logic

---

## Serializers (Django REST Framework)

**Purpose**: Validate request/response structure

**Request Serializer** (`serializers.py`):
```python
class MarkAttendanceRequestSerializer:
    Fields:
    - token (CharField, required)
    - scanned_student_id (CharField, required, regex validator)
    - latitude (DecimalField, required, max_digits=10, decimal_places=8)
    - longitude (DecimalField, required, max_digits=11, decimal_places=8)
    
    Validation:
    - All fields required (no blanks)
    - QR code matches ^[A-Z]{3}/[0-9]{6}$
    - Latitude: -90 to 90
    - Longitude: -180 to 180
    - Not (0, 0) coordinates
```

**Response Serializer** (`serializers.py`):
```python
class AttendanceResponseSerializer:
    Fields:
    - attendance_id (IntegerField)
    - student_profile_id (IntegerField)
    - session_id (IntegerField)
    - status (CharField, choices=["present", "late"])
    - is_within_radius (BooleanField)
    - time_recorded (DateTimeField, ISO 8601)
    - latitude (DecimalField)
    - longitude (DecimalField)
```

**Why Serializers**: DRF handles validation automatically, returns 400 with field errors

---

## URL Routing

**File**: `urls.py`

```python
urlpatterns = [
    path('api/v1/attendance/mark', MarkAttendanceView.as_view(), name='mark_attendance'),
]
```

**Why `/api/v1/`**: API versioning for future changes

**Methods Allowed**: POST only (no GET, PUT, DELETE)

**Why No Other Methods**:
- No GET (no endpoint to retrieve single attendance)
- No PUT/PATCH (immutable records)
- No DELETE (audit trail preservation)

**Priority: CRITICAL** - Immutability enforced at API level

---

# IMMUTABILITY RULES

**Priority: CRITICAL** - Data integrity

## No Update Endpoints

**Rules**:
- Attendance records cannot be modified after creation
- No PUT or PATCH endpoints
- No DELETE endpoint for students

**Why Immutable**:
- **Audit trail**: Historical record must not change
- **Anti-fraud**: Prevents post-hoc manipulation
- **Reporting integrity**: Reports based on original data

**Exceptions** (Admin Only):
- Lecturer can add manual attendance via admin panel
- Admin can soft-delete records (not exposed to students)

---

# FRONTEND CONSIDERATIONS

## Mobile-First Design

**Why Important**: Most students use mobile devices

**Frontend Flow**:
1. Email link opens in mobile browser
2. Prompt for camera permission (QR code scan)
3. Prompt for location permission (GPS)
4. Submit request
5. Show success/error message

**Error Handling**:
- Show clear error messages (use `error.message` from response)
- For 409 Conflict: Don't allow resubmission
- For 410 Gone: Explain token expired or session ended
- For 403 QR Mismatch: Warn about fraud detection

**Priority: HIGH** - User experience critical for adoption

---

## Security Considerations

**HTTPS Required**:
- Token in request body (plain text)
- GPS coordinates sensitive
- QR code data sensitive

**Rate Limiting**:
- Max 3 requests per minute per IP
- Prevents brute force token guessing
- Prevents spam submissions

**CORS Configuration**:
- Allow specific frontend domains only
- No wildcard (*) allowed

**Priority: CRITICAL** - Protect against attacks

---

# TESTING ENDPOINTS

## Manual Testing Checklist

**Valid Request**:
- ✅ 201 Created with attendance record
- ✅ Response includes `attendance_id`, `status`, `is_within_radius`

**Invalid Token**:
- ✅ 400 Bad Request with "Invalid attendance link"

**Expired Token**:
- ✅ 410 Gone with "Link has expired"

**QR Code Mismatch**:
- ✅ 403 Forbidden with fraud warning
- ✅ Logged for audit

**Duplicate Submission**:
- ✅ 409 Conflict with existing record details

**Session Ended**:
- ✅ 410 Gone with "Session has ended"

**Outside Radius**:
- ✅ 201 Created with `is_within_radius=false`, `status="late"`
- ✅ Record still created (not rejected)

**Priority: HIGH** - Cover all error scenarios

---

# API SUMMARY

## Endpoint Inventory

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/v1/attendance/mark` | POST | Token in body | Mark attendance |

**Only One Endpoint**: Attendance Recording is write-only for students

---

## Key Takeaways

1. **Token-based auth** (not JWT Bearer) - Token in request body
2. **Three-factor verification** - Token + QR + GPS in single request
3. **Comprehensive error handling** - 14 error codes covering all scenarios
4. **Immutable records** - No update/delete endpoints
5. **Duplicate prevention** - 409 Conflict on resubmission
6. **Clear user messages** - Every error has user-facing explanation
7. **Fraud detection** - QR mismatch logged for audit
8. **Status codes** - Semantic (201, 400, 403, 404, 409, 410, 425, 500)

---

**Status**: 📋 Complete API specification ready for implementation