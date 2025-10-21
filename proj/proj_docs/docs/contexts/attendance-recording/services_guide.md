# services_guide.md

Brief: Complete service layer specification for Attendance Recording. Five focused services with single responsibilities: TokenValidator (JWT), QRCodeValidator (anti-fraud), LocationValidator (Haversine), SessionValidator (eligibility), and AttendanceService (orchestration). Each service handles specific verification with brief explanations of security and business rules.

---

## Service Layer Purpose

**Why Services Matter**:
- **Three-factor verification**: Token + QR + Location must all pass
- **Security**: Each validator focuses on one authentication factor
- **Fraud prevention**: Multi-layer checks prevent impersonation
- **Testability**: Mock each validator independently
- **Maintainability**: Single responsibility per service

**Priority: CRITICAL** - Core security and business logic layer

---

# PART 1: TOKENVALIDATOR SERVICE

## Overview

**File**: `services/token_validator.py`

**Purpose**: Validate JWT tokens from email links and extract student/session data

**Why Separate Service**: 
- Token validation is complex (signature, expiry, format)
- Reused from Email Notification context (same JWT logic)
- Security-critical component deserving focused testing

**Dependencies**:
- PyJWT library (`import jwt`)
- Email Notification context (token generation spec)
- Secret key from settings

**Priority: CRITICAL** - First line of defense

---

## Method Specifications

### validate_and_decode_token(token: str) → dict

**Purpose**: Validate token and extract payload in one step

**Why Important**: Students use token from email as proof they were invited

**Validation Steps**:
1. **Format check**: Token has 3 parts (header.payload.signature)
2. **Signature verification**: Token signed with correct secret key
3. **Expiry check**: Token `exp` claim not past current time
4. **Required claims**: Payload contains `student_profile_id` and `session_id`

**Returns**: Dictionary with validated data:
```python
{
  "student_profile_id": 123,
  "session_id": 456,
  "iat": 1729339200,  # issued at
  "exp": 1729342800   # expires at
}
```

**Error Handling**:
- **Invalid signature** → Raise `InvalidTokenError`
  - Why: Token has been tampered with
  - HTTP Status: 400 Bad Request
  
- **Expired token** → Raise `ExpiredTokenError`
  - Why: Token past its expiry time
  - HTTP Status: 410 Gone (resource expired)
  - User-facing message: "Your attendance link has expired. Contact your lecturer."

- **Malformed token** → Raise `MalformedTokenError`
  - Why: Token doesn't match JWT format
  - HTTP Status: 400 Bad Request

- **Missing claims** → Raise `InvalidTokenError`
  - Why: Token doesn't contain required fields
  - HTTP Status: 400 Bad Request

**Security Note**: Never reveal secret key in error messages

### is_token_expired(token: str) → bool

**Purpose**: Quick expiry check without full validation

**Returns**: True if expired, False otherwise

**Use Case**: Provide better error message before attempting full validation

**Why Separate Method**: Distinguish between "expired" and "invalid" for user experience

---

## Integration with Email Notification Context

**Token Format Contract**:
- Algorithm: HS256 (same as Email Notification)
- Secret: Shared secret key (environment variable)
- Claims: Must include `student_profile_id`, `session_id`, `exp`

**Why Shared**: Email Notification generates; Attendance Recording validates (same spec)

---

# PART 2: QRCODEVALIDATOR SERVICE

## Overview

**File**: `services/qr_validator.py`

**Purpose**: Verify QR code format and match against token student

**Why Critical**: **Anti-fraud mechanism** - prevents students from using someone else's email link

**How It Works**:
1. Student receives email with token (contains Student A's ID)
2. Student must scan their own QR code (physical ID card)
3. System verifies: scanned QR code matches Student A
4. If mismatch → fraud attempt (Student B using Student A's email)

**Priority: CRITICAL** - Key security layer

---

## Method Specifications

### validate_qr_code_format(qr_data: str) → dict

**Purpose**: Parse and validate QR code format

**Expected Format**: `^[A-Z]{3}/[0-9]{6}$`

**Examples**:
- Valid: `BCS/234344` (Bachelor of Computer Science, student 234344)
- Valid: `MIT/123456`
- Invalid: `bcs/234344` (lowercase)
- Invalid: `BCS234344` (missing slash)
- Invalid: `BCS/12345` (only 5 digits)

**Returns**: Dictionary with parsed components:
```python
{
  "program_code": "BCS",
  "student_number": "234344",
  "full_student_id": "BCS/234344"
}
```

**Error Handling**:
- Invalid format → Raise `InvalidQRCodeFormatError`
- HTTP Status: 400 Bad Request
- User-facing message: "Invalid QR code format. Please scan your student ID card."

**Why Format Validation**: Ensure data quality, detect spoofed QR codes

### verify_qr_matches_token(scanned_student_id: str, token_student_profile_id: int) → bool

**Purpose**: Anti-fraud check - ensure QR code matches token student

**Workflow**:
1. Extract `student_profile_id` from validated token
2. Query `StudentProfile` by `student_profile_id`
3. Get `StudentProfile.student_id` (e.g., "BCS/234344")
4. Compare: `scanned_student_id == StudentProfile.student_id`

**Returns**: 
- `True` if match (valid)
- `False` if mismatch (fraud attempt)

**Error Handling**:
- Student not found → Raise `StudentNotFoundError`
- Mismatch → Raise `QRCodeMismatchError`
  - HTTP Status: 403 Forbidden
  - User-facing message: "This QR code does not match your attendance link. Please use your own student ID."
  - **Security Log**: Log this attempt for audit (potential fraud)

**Why Critical**: 
- Without this check, Student A could forward email to Student B
- Student B could mark attendance using Student A's token
- QR code forces physical ID card presence

**Example Fraud Scenario Prevented**:
```
Email sent to: Student A (token contains student_profile_id=123)
Student A forwards email to Student B
Student B clicks link, scans their own QR (BCS/567890)
System checks: token says student_profile_id=123 (Student A's ID is BCS/234344)
QR code says: BCS/567890 (Student B)
Mismatch detected → Attendance blocked, fraud logged
```

---

# PART 3: LOCATIONVALIDATOR SERVICE

## Overview

**File**: `services/location_validator.py`

**Purpose**: Calculate distance between two GPS coordinates and verify 30m radius

**Why Important**: Proves physical presence at session location

**Algorithm**: Haversine formula for accurate distance on Earth's surface

**Priority: HIGH** - Physical presence verification

---

## Method Specifications

### calculate_distance(lat1: Decimal, lon1: Decimal, lat2: Decimal, lon2: Decimal) → float

**Purpose**: Calculate distance between two GPS coordinates

**Algorithm**: Haversine formula
- Accounts for Earth's curvature
- More accurate than simple Euclidean distance
- Standard for GPS distance calculations

**Haversine Formula** (conceptual):
```
Convert degrees to radians
Calculate differences in latitude and longitude
Apply trigonometric functions (sin, cos, asin)
Multiply by Earth's radius (6,371,000 meters)
Result: Distance in meters
```

**Why Haversine**:
- **Accuracy**: Correct for spherical surface (Earth)
- **Standard**: Used by GPS systems worldwide
- **Precision**: Accurate to within 0.5% for distances up to few hundred km

**Returns**: Distance in meters (float)

**Example**:
```python
# Session at University Main Gate
session_lat = Decimal('-1.28333412')
session_lon = Decimal('36.81666588')

# Student near library (50m away)
student_lat = Decimal('-1.28380000')
student_lon = Decimal('36.81700000')

distance = calculate_distance(session_lat, session_lon, student_lat, student_lon)
# Returns: 52.3 meters
```

**Performance**: Fast enough for real-time validation (milliseconds)

### is_within_radius(student_lat: Decimal, student_lon: Decimal, session_lat: Decimal, session_lon: Decimal, radius_meters: int = 30) → bool

**Purpose**: Check if student is within acceptable distance

**Parameters**:
- `radius_meters`: Default 30 (configurable for testing)

**Logic**:
```python
distance = calculate_distance(student_lat, student_lon, session_lat, session_lon)
return distance <= radius_meters
```

**Returns**: 
- `True` if within radius
- `False` if outside radius

**Important**: Even if `False`, attendance is still recorded with flag `is_within_radius=False`

**Why Not Blocker**: 
- GPS inaccuracy (devices vary)
- Building structure (signal interference)
- Indoor vs outdoor location
- Lecturer can review and excuse

**Example Scenarios**:
```
Scenario 1: Student in classroom (15m from lecturer)
Result: is_within_radius=True, status="present" ✅

Scenario 2: Student in hallway outside (40m away)
Result: is_within_radius=False, status="late" ⚠️
Attendance recorded, lecturer reviews

Scenario 3: Student at home (5km away - GPS spoofing attempt)
Result: is_within_radius=False, obvious fraud 🚨
Attendance recorded with flag for investigation
```

### validate_coordinates(latitude: Decimal, longitude: Decimal) → None

**Purpose**: Check GPS coordinates are valid

**Validations**:
- Latitude: -90 to 90 degrees
- Longitude: -180 to 180 degrees
- Not (0, 0) - default/invalid coordinates
- Not NULL

**Error Handling**:
- Invalid range → Raise `InvalidCoordinatesError`
- HTTP Status: 400 Bad Request
- User-facing message: "Invalid GPS coordinates. Please enable location services."

**Why (0, 0) Check**: 
- (0, 0) is in the Gulf of Guinea (middle of ocean)
- Often default value when GPS fails
- Filters out bad data

---

# PART 4: SESSIONVALIDATOR SERVICE

## Overview

**File**: `services/session_validator.py`

**Purpose**: Validate session state and student eligibility

**Why Separate Service**: Complex cross-context validation deserves focused logic

**Priority: HIGH** - Ensure students only mark attendance when eligible

---

## Method Specifications

### validate_session_active(session_id: int) → dict

**Purpose**: Check if session is accepting attendance

**Validation Steps**:
1. **Session exists**: Query session by ID
2. **Time window check**: `session.time_created <= now <= session.time_ended`
3. **Not ended**: Session hasn't passed end time

**Returns**: Dictionary with session details:
```python
{
  "session_id": 123,
  "is_active": True,
  "time_created": "2025-10-25T08:00:00Z",
  "time_ended": "2025-10-25T10:00:00Z",
  "program_id": 1,
  "stream_id": 25
}
```

**Error Handling**:
- Session not found → Raise `SessionNotFoundError` (404)
- Session not started → Raise `SessionNotStartedError` (425 Too Early)
  - User message: "Session has not started yet. Please wait."
- Session ended → Raise `SessionEndedError` (410 Gone)
  - User message: "Session has ended. Attendance window closed."

**Why Time Window Critical**: Prevents marking attendance before session or after it ends

### validate_student_eligibility(student_profile_id: int, session_id: int) → None

**Purpose**: Check if student is eligible to attend this session

**Cross-Context Checks**:
1. **Student exists and is active**
   - Query `StudentProfile` by ID
   - Check `user.is_active = True`
   
2. **Program match**
   - Student's `program_id` must equal session's `program_id`
   - Why: Can't attend sessions for other programs
   
3. **Stream match** (if session has stream targeting)
   - If `session.stream_id` is NULL: All program students eligible
   - If `session.stream_id` is set: Student's `stream_id` must match
   - Why: Stream-specific sessions only for that stream

**Error Handling**:
- Student not found → Raise `StudentNotFoundError` (404)
- Inactive student → Raise `InactiveStudentError` (403)
  - User message: "Your account is inactive. Contact administration."
- Program mismatch → Raise `ProgramMismatchError` (403)
  - User message: "You are not enrolled in this program."
- Stream mismatch → Raise `StreamMismatchError` (403)
  - User message: "This session is not for your stream."

**Why Eligibility Critical**: 
- Prevent students from attending wrong sessions
- Enforce stream targeting
- Maintain data integrity

**Example Eligibility Scenarios**:
```
Scenario 1: Session for BCS Year 2 Stream A
Student: BCS Year 2 Stream A → Eligible ✅

Scenario 2: Session for BCS Year 2 Stream A  
Student: BCS Year 2 Stream B → NOT Eligible ❌ (stream mismatch)

Scenario 3: Session for BCS (no stream, entire program)
Student: BCS Year 2 Stream A → Eligible ✅
Student: BCS Year 3 Stream B → Eligible ✅

Scenario 4: Session for BCS
Student: MIT (different program) → NOT Eligible ❌ (program mismatch)
```

---

# PART 5: ATTENDANCESERVICE (ORCHESTRATOR)

## Overview

**File**: `services/attendance_service.py`

**Purpose**: Orchestrate all validators and create attendance record

**Why Separate**: High-level workflow coordination, integrates all other services

**Priority: CRITICAL** - Core business logic

---

## Dependencies

```python
- TokenValidator (JWT validation)
- QRCodeValidator (anti-fraud)
- LocationValidator (distance calculation)
- SessionValidator (session state, eligibility)
- AttendanceRepository (data access)
```

**Why Multiple Dependencies**: Each validator has single responsibility; orchestrator combines them

---

## Method Specifications

### mark_attendance(request_data: dict) → dict

**Purpose**: Complete attendance marking workflow with all verifications

**Input**: Dictionary from API request:
```python
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "scanned_student_id": "BCS/234344",
  "latitude": "-1.28334000",
  "longitude": "36.81667000"
}
```

**Workflow Steps** (each can raise exception to abort):

1. **Validate Token** → Get student_profile_id and session_id
   ```python
   token_data = token_validator.validate_and_decode_token(token)
   student_profile_id = token_data["student_profile_id"]
   session_id = token_data["session_id"]
   ```

2. **Verify QR Code** → Anti-fraud check
   ```python
   qr_validator.verify_qr_matches_token(scanned_student_id, student_profile_id)
   ```

3. **Validate Session** → Get session details and check active
   ```python
   session_data = session_validator.validate_session_active(session_id)
   ```

4. **Check Eligibility** → Program/stream match
   ```python
   session_validator.validate_student_eligibility(student_profile_id, session_id)
   ```

5. **Check Duplicate** → Prevent double submission
   ```python
   if attendance_repo.exists_for_student_and_session(student_profile_id, session_id):
       raise DuplicateAttendanceError("Already marked")
   ```

6. **Validate Coordinates** → GPS data quality
   ```python
   location_validator.validate_coordinates(latitude, longitude)
   ```

7. **Calculate Distance** → 30m radius check
   ```python
   is_within_radius = location_validator.is_within_radius(
       student_lat=latitude,
       student_lon=longitude,
       session_lat=session_data["latitude"],
       session_lon=session_data["longitude"]
   )
   ```

8. **Determine Status** → Present vs late
   ```python
   status = determine_status(is_within_radius, time_recorded, session_data)
   ```

9. **Create Record** → Save to database
   ```python
   attendance = attendance_repo.create({
       "student_profile_id": student_profile_id,
       "session_id": session_id,
       "latitude": latitude,
       "longitude": longitude,
       "status": status,
       "is_within_radius": is_within_radius
   })
   ```

10. **Return Success** → Response with attendance details

**Returns**: Success dictionary:
```python
{
  "success": True,
  "attendance_id": 501,
  "status": "present",
  "is_within_radius": True,
  "time_recorded": "2025-10-25T08:05:23Z",
  "message": "Attendance marked successfully"
}
```

**Error Handling**: Any step failure raises specific exception, workflow stops

**Why Sequential**: Each step builds on previous; fail fast on first error

### determine_status(is_within_radius: bool, time_recorded: datetime, session_data: dict) → str

**Purpose**: Classify attendance as "present" or "late"

**Logic**:
```python
if is_within_radius:
    # Within radius - check timing
    session_duration = session_data["time_ended"] - session_data["time_created"]
    grace_period = session_duration * 0.25  # First 25% of session
    
    if time_recorded <= session_data["time_created"] + grace_period:
        return "present"
    else:
        return "late"  # Marked late in session
else:
    # Outside radius - always late
    return "late"
```

**Business Rules**:
- Within radius + early → "present"
- Within radius + late → "late"
- Outside radius → "late" (regardless of timing)

**Why Grace Period**: Allow students arriving slightly late without penalty

---

## Service Collaboration Pattern

**How services work together**:

```
AttendanceService.mark_attendance()
    ↓ calls
TokenValidator.validate_and_decode_token()
    ↓ calls
QRCodeValidator.verify_qr_matches_token()
    ↓ calls
SessionValidator.validate_session_active()
    ↓ calls
SessionValidator.validate_student_eligibility()
    ↓ calls
LocationValidator.is_within_radius()
    ↓ calls
AttendanceRepository.create()
    ↓ returns
Success response
```

**Why This Pattern**:
- Each service single responsibility
- Easy to test in isolation (mock dependencies)
- Clear error boundaries (know which check failed)
- Can add more validators without changing orchestrator structure

---

## File Organization

**Priority: MEDIUM** - Maintainability

```
attendance_recording/
├── services/
│   ├── __init__.py
│   ├── token_validator.py               # TokenValidator
│   ├── qr_validator.py                  # QRCodeValidator
│   ├── location_validator.py            # LocationValidator
│   ├── session_validator.py             # SessionValidator
│   └── attendance_service.py            # AttendanceService (orchestrator)
├── repositories/
│   └── attendance_repository.py
├── handlers/
│   └── mark_attendance_handler.py       # API layer handler
└── tests/
    ├── test_token_validator.py
    ├── test_qr_validator.py
    ├── test_location_validator.py
    ├── test_session_validator.py
    └── test_attendance_service.py
```

**Why Five Separate Service Files**:
- Clear separation of concerns
- Each file <200 lines (maintainable size)
- Easy to locate specific validation logic
- Can test each validator independently

---

## Error Handling and Domain Exceptions

**Priority: CRITICAL** - Security and user experience

### Custom Exceptions

```python
# attendance_recording/exceptions.py

class AttendanceRecordingError(Exception):
    """Base exception"""
    pass

# Token errors
class InvalidTokenError(AttendanceRecordingError):
    """Token signature invalid"""
    pass

class ExpiredTokenError(AttendanceRecordingError):
    """Token has expired"""
    pass

class MalformedTokenError(AttendanceRecordingError):
    """Token format invalid"""
    pass

# QR code errors
class InvalidQRCodeFormatError(AttendanceRecordingError):
    """QR code doesn't match expected format"""
    pass

class QRCodeMismatchError(AttendanceRecordingError):
    """QR code doesn't match token student (fraud attempt)"""
    pass

# Location errors
class InvalidCoordinatesError(AttendanceRecordingError):
    """GPS coordinates out of valid range"""
    pass

# Session errors
class SessionNotFoundError(AttendanceRecordingError):
    """Session doesn't exist"""
    pass

class SessionNotStartedError(AttendanceRecordingError):
    """Session hasn't started yet"""
    pass

class SessionEndedError(AttendanceRecordingError):
    """Session has ended"""
    pass

# Eligibility errors
class StudentNotFoundError(AttendanceRecordingError):
    """Student doesn't exist"""
    pass

class InactiveStudentError(AttendanceRecordingError):
    """Student account inactive"""
    pass

class ProgramMismatchError(AttendanceRecordingError):
    """Student not in session's program"""
    pass

class StreamMismatchError(AttendanceRecordingError):
    """Student not in session's stream"""
    pass

# Duplicate error
class DuplicateAttendanceError(AttendanceRecordingError):
    """Attendance already marked"""
    pass
```

### Error Mapping to HTTP Status

Services raise domain exceptions → Handler maps to HTTP:

| Exception | HTTP Status | User-Facing Message |
|-----------|-------------|---------------------|
| InvalidTokenError | 400 Bad Request | "Invalid attendance link" |
| ExpiredTokenError | 410 Gone | "Link expired. Contact lecturer." |
| QRCodeMismatchError | 403 Forbidden | "QR code doesn't match your link" |
| SessionEndedError | 410 Gone | "Session has ended" |
| DuplicateAttendanceError | 409 Conflict | "Already marked attendance" |
| ProgramMismatchError | 403 Forbidden | "Not enrolled in this program" |
| InvalidCoordinatesError | 400 Bad Request | "Enable location services" |

**Why Domain Exceptions**: Services stay technology-agnostic (no HTTP knowledge)

---

## Service Summary

### TokenValidator (JWT Security)
- `validate_and_decode_token` - Verify JWT and extract data
- `is_token_expired` - Check expiry

### QRCodeValidator (Anti-Fraud)
- `validate_qr_code_format` - Parse and validate format
- `verify_qr_matches_token` - Match QR to token student

### LocationValidator (Physical Presence)
- `calculate_distance` - Haversine formula
- `is_within_radius` - 30m radius check
- `validate_coordinates` - GPS data quality

### SessionValidator (Eligibility)
- `validate_session_active` - Time window check
- `validate_student_eligibility` - Program/stream match

### AttendanceService (Orchestration)
- `mark_attendance` - Complete workflow
- `determine_status` - Present vs late classification

---

**Status**: 📋 Complete service specification ready for implementation

**Key Takeaways**:
1. **Five focused services** (Token, QR, Location, Session, Orchestration)
2. **Three-factor verification** (JWT + QR + GPS)
3. **Haversine formula** for accurate distance
4. **QR code anti-fraud** (prevents email forwarding)
5. **Sequential workflow** (fail fast on first error)