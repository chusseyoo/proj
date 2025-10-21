# testing_guide.md

Brief: Complete testing strategy for Attendance Recording context. Six parts plus fixtures covering three-factor verification (JWT + QR + GPS), Haversine distance calculations, fraud detection, duplicate prevention, cross-context integration, and edge cases. Focus on security-critical components.

---

## Testing Strategy Overview

**Why Testing Critical**:
- **Security**: Three-factor verification must be bulletproof
- **Anti-fraud**: QR code mismatch detection prevents impersonation
- **GPS accuracy**: Haversine formula must calculate correctly
- **Duplicate prevention**: Unique constraint enforcement
- **Data integrity**: Immutable records must stay immutable

**Priority: CRITICAL** - Security-critical system requires comprehensive testing

**Testing Framework**: pytest with Django test database

**Excluded Parts**:
- Part 7: Performance testing (out of scope)

---

# PART 1: MODEL TESTS

## Test File

**File**: `tests/test_models.py`

**Purpose**: Validate Attendance model constraints, defaults, and immutability

**Priority: HIGH** - Foundation layer

---

## Test Cases

### test_create_attendance_record_success

**Purpose**: Verify valid attendance creation

**Setup**:
- Create StudentProfile, Session (prerequisites)
- Valid GPS coordinates within range

**Assertions**:
- Record created successfully
- `time_recorded` auto-set to current time
- `status` set correctly ("present" or "late")
- `is_within_radius` boolean recorded
- `latitude` and `longitude` stored as Decimal

**Why Important**: Baseline functionality test

---

### test_unique_constraint_student_session

**Purpose**: Enforce one attendance per student per session

**Setup**:
- Create first attendance record
- Attempt duplicate with same student_profile_id and session_id

**Expected**: IntegrityError (database-level constraint violation)

**Why Critical**: **Duplicate prevention** - prevents double submissions

**Assertion**: Exception raised with unique constraint name in message

---

### test_cascade_delete_student

**Purpose**: Verify CASCADE on student_profile FK

**Setup**:
- Create attendance record
- Delete student profile

**Expected**: Attendance record also deleted

**Why Important**: Data integrity when student removed from system

---

### test_cascade_delete_session

**Purpose**: Verify CASCADE on session FK

**Setup**:
- Create attendance record
- Delete session

**Expected**: Attendance record also deleted

**Why Important**: Clean up attendance when session removed

---

### test_latitude_longitude_precision

**Purpose**: Validate Decimal precision storage

**Setup**:
- Create attendance with high-precision coordinates
- Example: `latitude=Decimal('-1.28334567')` (8 decimals)

**Assertions**:
- Stored value matches input exactly
- No floating-point rounding errors
- Database stores as Decimal(10,8) and Decimal(11,8)

**Why Critical**: GPS accuracy depends on decimal precision

---

### test_status_field_choices

**Purpose**: Validate status field accepts only "present" or "late"

**Setup**:
- Attempt to create with invalid status (e.g., "absent")

**Expected**: Validation error or constraint violation

**Why Important**: Enforce valid status values

---

### test_time_recorded_auto_now

**Purpose**: Verify auto-set timestamp

**Setup**:
- Create record without specifying time_recorded

**Assertions**:
- Field auto-populated
- Timestamp within 1 second of current time (UTC)

**Why Important**: Accurate audit trail

---

### test_immutable_record_no_update

**Purpose**: Attendance records should not be updatable

**Setup**:
- Create attendance record
- Attempt to modify status or GPS coordinates

**Expected**: Application-level validation prevents update (or test documents intent)

**Why Critical**: **Immutability** - audit trail preservation

**Note**: Django doesn't enforce immutability at model level; document expected behavior

---

# PART 2: REPOSITORY TESTS

## Test File

**File**: `tests/test_repositories.py`

**Purpose**: Validate repository methods, especially duplicate detection and queries

**Priority: CRITICAL** - Duplicate detection is security-critical

---

## Test Cases

### test_create_attendance

**Purpose**: Basic repository create operation

**Setup**:
- Prepare valid attendance data dict

**Assertions**:
- Record created and returned
- ID assigned (primary key)

---

### test_exists_for_student_and_session_true

**Purpose**: Duplicate detection - record exists

**Setup**:
- Create attendance record for Student A, Session 1
- Call `exists_for_student_and_session(student_profile_id, session_id)`

**Expected**: Returns `True`

**Why Critical**: **Prevents duplicates** - core security function

---

### test_exists_for_student_and_session_false

**Purpose**: Duplicate detection - record doesn't exist

**Setup**:
- No attendance for Student A, Session 1
- Call `exists_for_student_and_session(student_profile_id, session_id)`

**Expected**: Returns `False`

**Why Important**: Allows first-time submissions

---

### test_get_by_session

**Purpose**: Query all attendance for a session

**Setup**:
- Create 3 attendance records for Session 1
- Create 2 attendance records for Session 2

**Assertions**:
- `get_by_session(session_1_id)` returns 3 records
- `get_by_session(session_2_id)` returns 2 records

**Why Important**: Lecturer views session attendance

---

### test_count_by_session

**Purpose**: Count attendance for reporting

**Setup**:
- Create 5 attendance records for Session 1

**Assertions**:
- `count_by_session(session_1_id)` returns 5

**Why Important**: Quick statistics without loading all records

---

### test_get_by_student

**Purpose**: Query student's attendance history

**Setup**:
- Create 4 attendance records for Student A across different sessions

**Assertions**:
- `get_by_student(student_profile_id)` returns 4 records

**Why Important**: Student views their attendance history

---

### test_get_students_outside_radius

**Purpose**: Reporting - find students marked outside 30m radius

**Setup**:
- Create 3 records with `is_within_radius=True`
- Create 2 records with `is_within_radius=False` for same session

**Assertions**:
- `get_students_outside_radius(session_id)` returns 2 records

**Why Important**: Lecturer reviews suspicious attendance for GPS spoofing

---

### test_get_attendance_summary_by_session

**Purpose**: Summary statistics for session

**Setup**:
- Session 1: 10 "present", 3 "late"
- Session 2: 5 "present", 1 "late"

**Assertions**:
- Summary includes total count, present count, late count
- Accurate for each session

**Why Important**: Dashboard reporting

---

# PART 3: SERVICE TESTS

## Test File

**File**: `tests/test_services.py`

**Purpose**: Validate business logic in all five services

**Priority: CRITICAL** - Core security and fraud detection

---

## TokenValidator Tests

### test_validate_and_decode_token_success

**Purpose**: Valid token decoded correctly

**Setup**:
- Generate valid JWT with required claims (student_profile_id, session_id, exp)

**Assertions**:
- Token decoded without error
- Claims extracted correctly

---

### test_validate_token_expired

**Purpose**: Expired token rejected

**Setup**:
- Generate token with `exp` in the past

**Expected**: `ExpiredTokenError` raised

**Why Critical**: Prevents use of old/forwarded links

---

### test_validate_token_invalid_signature

**Purpose**: Tampered token rejected

**Setup**:
- Generate token, modify signature part

**Expected**: `InvalidTokenError` raised

**Why Critical**: **Security** - prevents token forgery

---

### test_validate_token_missing_claims

**Purpose**: Incomplete token rejected

**Setup**:
- Generate token without `student_profile_id` or `session_id`

**Expected**: `InvalidTokenError` raised

**Why Important**: Ensure all required data present

---

## QRCodeValidator Tests

### test_validate_qr_code_format_valid

**Purpose**: Correct format accepted

**Setup**:
- QR data: `"BCS/234344"`

**Assertions**:
- Parsed into `{"program_code": "BCS", "student_number": "234344"}`

---

### test_validate_qr_code_format_invalid

**Purpose**: Invalid formats rejected

**Test Cases**:
- Lowercase: `"bcs/234344"` → Error
- No slash: `"BCS234344"` → Error
- Wrong digits: `"BCS/12345"` → Error

**Expected**: `InvalidQRCodeFormatError` for each

**Why Important**: Data quality enforcement

---

### test_verify_qr_matches_token_success

**Purpose**: QR code matches token student

**Setup**:
- Token contains `student_profile_id=123`
- StudentProfile 123 has `student_id="BCS/234344"`
- Scanned QR: `"BCS/234344"`

**Expected**: Validation passes (no exception)

---

### test_verify_qr_matches_token_mismatch

**Purpose**: **Anti-fraud detection** - QR doesn't match token

**Setup**:
- Token contains `student_profile_id=123` (Student A: "BCS/234344")
- Scanned QR: `"MIT/123456"` (Student B)

**Expected**: `QRCodeMismatchError` raised

**Why Critical**: **Prevents email forwarding fraud** - Student B cannot use Student A's link

**Security**: Test that fraud attempt is logged

---

## LocationValidator Tests

### test_calculate_distance_haversine

**Purpose**: Haversine formula calculates correctly

**Test Cases**:
- Same coordinates → 0 meters
- Known distance (e.g., 50m between two points) → ~50 meters
- Long distance (e.g., 5km) → ~5000 meters

**Assertions**:
- Distance within acceptable margin (±1 meter due to floating-point)

**Why Critical**: GPS validation accuracy depends on correct calculation

---

### test_is_within_radius_true

**Purpose**: Student within 30m radius

**Setup**:
- Session at (lat1, lon1)
- Student at (lat2, lon2) - 15m away

**Expected**: `is_within_radius()` returns `True`

---

### test_is_within_radius_false

**Purpose**: Student outside 30m radius

**Setup**:
- Session at (lat1, lon1)
- Student at (lat2, lon2) - 50m away

**Expected**: `is_within_radius()` returns `False`

**Note**: Attendance still recorded, just flagged

---

### test_validate_coordinates_valid

**Purpose**: Valid GPS coordinates accepted

**Test Cases**:
- Latitude: -90 to 90
- Longitude: -180 to 180

**Expected**: No exception raised

---

### test_validate_coordinates_invalid

**Purpose**: Invalid coordinates rejected

**Test Cases**:
- Latitude > 90 → Error
- Longitude < -180 → Error
- (0, 0) → Error (likely default/invalid)

**Expected**: `InvalidCoordinatesError` for each

**Why Important**: Data quality, prevent bad GPS data

---

## SessionValidator Tests

### test_validate_session_active_success

**Purpose**: Active session validation passes

**Setup**:
- Session with `time_created` in past, `time_ended` in future

**Expected**: Validation passes, session details returned

---

### test_validate_session_not_started

**Purpose**: Session in future rejected

**Setup**:
- Session with `time_created` in future

**Expected**: `SessionNotStartedError` raised

**Why Important**: Prevent early submissions

---

### test_validate_session_ended

**Purpose**: Past session rejected

**Setup**:
- Session with `time_ended` in past

**Expected**: `SessionEndedError` raised

**Why Important**: Enforce attendance window

---

### test_validate_student_eligibility_success

**Purpose**: Eligible student allowed

**Setup**:
- Student in BCS, Session for BCS (same program)
- Session stream matches student stream (or NULL)

**Expected**: Validation passes

---

### test_validate_student_eligibility_program_mismatch

**Purpose**: Different program rejected

**Setup**:
- Student in BCS, Session for MIT

**Expected**: `ProgramMismatchError` raised

**Why Important**: Prevent cross-program attendance

---

### test_validate_student_eligibility_stream_mismatch

**Purpose**: Wrong stream rejected

**Setup**:
- Student in Stream A, Session targets Stream B

**Expected**: `StreamMismatchError` raised

**Why Important**: Enforce stream targeting

---

### test_validate_student_eligibility_inactive_student

**Purpose**: Inactive student rejected

**Setup**:
- Student with `user.is_active=False`

**Expected**: `InactiveStudentError` raised

**Why Important**: Suspended students cannot mark attendance

---

## AttendanceService Tests (Orchestration)

### test_mark_attendance_success

**Purpose**: Complete happy path workflow

**Setup**:
- Valid token
- Matching QR code
- Active session
- Eligible student
- No duplicate
- Valid GPS coordinates

**Expected**: Attendance record created, success response returned

**Assertions**:
- Record created in database
- Status determined correctly
- `is_within_radius` calculated correctly

**Why Critical**: End-to-end integration of all validators

---

### test_mark_attendance_duplicate

**Purpose**: Duplicate prevention

**Setup**:
- Create first attendance
- Attempt second with same student/session

**Expected**: `DuplicateAttendanceError` raised before creating record

**Why Critical**: Enforce unique constraint at service level

---

### test_mark_attendance_token_expired

**Purpose**: Workflow stops on expired token

**Setup**:
- Expired token

**Expected**: `ExpiredTokenError` raised, no record created

**Why Important**: Fail fast on first validation

---

### test_mark_attendance_qr_mismatch

**Purpose**: Workflow stops on fraud attempt

**Setup**:
- Valid token for Student A
- QR code for Student B

**Expected**: `QRCodeMismatchError` raised, fraud logged, no record created

**Why Critical**: **Fraud detection** - prevent impersonation

---

### test_mark_attendance_outside_radius

**Purpose**: Record created even if outside radius

**Setup**:
- Valid token, QR, session, eligibility
- GPS coordinates 50m away (outside 30m radius)

**Expected**: 
- Attendance record created
- `is_within_radius=False`
- `status="late"`

**Why Important**: Document behavior - not rejected, just flagged

---

### test_determine_status_present

**Purpose**: Status logic - "present"

**Setup**:
- Within radius
- Marked within first 25% of session

**Expected**: `status="present"`

---

### test_determine_status_late_timing

**Purpose**: Status logic - "late" due to timing

**Setup**:
- Within radius
- Marked after 25% of session

**Expected**: `status="late"`

---

### test_determine_status_late_location

**Purpose**: Status logic - "late" due to location

**Setup**:
- Outside radius (regardless of timing)

**Expected**: `status="late"`

---

# PART 4: API/HANDLER TESTS

## Test File

**File**: `tests/test_handlers.py`

**Purpose**: HTTP layer - request validation, response formatting, exception mapping

**Priority: HIGH** - User-facing interface

---

## Test Cases

### test_mark_attendance_success_201

**Purpose**: Valid request returns 201 Created

**Setup**:
- Mock successful service response
- Valid request payload

**Assertions**:
- HTTP 201 status
- Response contains attendance data
- `success=true` in response

---

### test_mark_attendance_invalid_token_400

**Purpose**: Invalid token returns 400 Bad Request

**Setup**:
- Malformed token (not JWT format)

**Expected**: 
- HTTP 400
- Error code: `INVALID_TOKEN`
- User-friendly message

---

### test_mark_attendance_qr_mismatch_403

**Purpose**: QR mismatch returns 403 Forbidden

**Setup**:
- Mock `QRCodeMismatchError` from service

**Expected**:
- HTTP 403
- Error code: `QR_CODE_MISMATCH`
- Message warns about fraud

---

### test_mark_attendance_duplicate_409

**Purpose**: Duplicate returns 409 Conflict

**Setup**:
- Mock `DuplicateAttendanceError` from service

**Expected**:
- HTTP 409
- Error code: `DUPLICATE_ATTENDANCE`
- Shows existing attendance details

---

### test_mark_attendance_token_expired_410

**Purpose**: Expired token returns 410 Gone

**Setup**:
- Mock `ExpiredTokenError` from service

**Expected**:
- HTTP 410
- Error code: `TOKEN_EXPIRED`
- Message instructs to contact lecturer

---

### test_mark_attendance_session_ended_410

**Purpose**: Ended session returns 410 Gone

**Setup**:
- Mock `SessionEndedError` from service

**Expected**:
- HTTP 410
- Error code: `SESSION_ENDED`

---

### test_mark_attendance_session_not_started_425

**Purpose**: Early submission returns 425 Too Early

**Setup**:
- Mock `SessionNotStartedError` from service

**Expected**:
- HTTP 425
- Error code: `SESSION_NOT_STARTED`

---

### test_mark_attendance_missing_field_400

**Purpose**: Missing required field returns 400

**Setup**:
- Request without `latitude` field

**Expected**:
- HTTP 400
- Error indicates missing field

---

### test_mark_attendance_invalid_qr_format_400

**Purpose**: Invalid QR format returns 400

**Setup**:
- QR code: `"bcs/234344"` (lowercase)

**Expected**:
- HTTP 400
- Error code: `INVALID_QR_FORMAT`

---

### test_mark_attendance_program_mismatch_403

**Purpose**: Program mismatch returns 403

**Setup**:
- Mock `ProgramMismatchError` from service

**Expected**:
- HTTP 403
- Error code: `PROGRAM_MISMATCH`

---

### test_response_format_structure

**Purpose**: Response envelope consistent

**Setup**:
- Valid request

**Assertions**:
- Response has `success`, `data`, `message` fields
- `data` contains all attendance fields
- ISO 8601 timestamp format

---

# PART 5: INTEGRATION TESTS

## Test File

**File**: `tests/test_integration.py`

**Purpose**: End-to-end workflows across contexts

**Priority: CRITICAL** - Validate cross-context dependencies

---

## Test Cases

### test_full_attendance_flow_end_to_end

**Purpose**: Complete user journey from email to attendance

**Workflow**:
1. Session Management: Create session
2. Email Notifications: Generate notification with token
3. Attendance Recording: Use token to mark attendance

**Assertions**:
- Attendance record created
- Linked correctly to session and student
- Token validation works across contexts

**Why Critical**: Validates three-context integration

---

### test_token_from_email_notification_context

**Purpose**: Token contract between contexts

**Setup**:
- Email Notification generates token (HS256, required claims)
- Attendance Recording validates same token

**Assertions**:
- Token generated by Email context is valid for Attendance context
- Claims decoded correctly

**Why Important**: Ensure shared JWT specification

---

### test_session_validation_with_session_management_context

**Purpose**: Session state validation across contexts

**Setup**:
- Session Management marks session as ended
- Attendance Recording checks session active

**Expected**: `SessionEndedError` raised

**Why Important**: Real-time session state synchronization

---

### test_student_eligibility_with_academic_structure_context

**Purpose**: Cross-context program/stream validation

**Setup**:
- Academic Structure: Student in BCS Stream A
- Session Management: Session for BCS Stream B
- Attendance Recording: Validate eligibility

**Expected**: `StreamMismatchError` raised

**Why Important**: Enforce enrollment rules across contexts

---

### test_duplicate_prevention_across_multiple_requests

**Purpose**: Race condition handling

**Setup**:
- Simulate concurrent requests for same student/session

**Expected**: Only one record created, second request gets 409 Conflict

**Why Important**: Database-level unique constraint prevents duplicates

---

# PART 6: EDGE CASES AND ERROR SCENARIOS

## Test File

**File**: `tests/test_edge_cases.py`

**Purpose**: Unusual scenarios, boundary conditions, security edge cases

**Priority: HIGH** - Robustness testing

---

## Test Cases

### test_gps_coordinates_at_exact_30m_boundary

**Purpose**: Boundary condition for radius

**Setup**:
- Student exactly 30.0 meters away

**Expected**: `is_within_radius=True` (inclusive boundary)

**Why Important**: Clarify boundary behavior

---

### test_gps_coordinates_equator_crossing

**Purpose**: Haversine at equator (latitude 0)

**Setup**:
- Session at (0, 36.8), Student at (0.0001, 36.8)

**Expected**: Distance calculated correctly (no special case bug)

---

### test_gps_coordinates_prime_meridian_crossing

**Purpose**: Haversine at longitude 0

**Setup**:
- Session at (-1.28, 0), Student at (-1.28, 0.0001)

**Expected**: Distance calculated correctly

---

### test_gps_spoofing_far_distance

**Purpose**: Obvious GPS spoof detection

**Setup**:
- Session in Nairobi (-1.28, 36.81)
- Student GPS claims London (51.5, -0.12) - ~6500km away

**Expected**: 
- `is_within_radius=False`
- Record created with flag (for review)

**Why Important**: Document that extreme distances are recorded, not rejected

---

### test_token_expiry_one_second_boundary

**Purpose**: Token expires exactly at boundary

**Setup**:
- Token with `exp` = current_time + 1 second
- Wait 1 second, attempt validation

**Expected**: `ExpiredTokenError` raised

**Why Important**: Clarify expiry is not inclusive

---

### test_qr_code_case_sensitivity

**Purpose**: Enforce uppercase requirement

**Setup**:
- QR code: `"bcs/234344"` (lowercase)

**Expected**: `InvalidQRCodeFormatError` raised

**Why Important**: Format validation is case-sensitive

---

### test_qr_code_whitespace

**Purpose**: Reject whitespace in QR data

**Setup**:
- QR code: `"BCS/ 234344"` (space in number)

**Expected**: `InvalidQRCodeFormatError` raised

---

### test_inactive_student_attempt

**Purpose**: Suspended student cannot mark attendance

**Setup**:
- Student with `user.is_active=False`
- Valid token, QR, session

**Expected**: `InactiveStudentError` raised

**Why Important**: Enforce account status

---

### test_deleted_student_profile

**Purpose**: Deleted student cannot attend

**Setup**:
- Token contains `student_profile_id` for deleted student

**Expected**: `StudentNotFoundError` raised

---

### test_deleted_session

**Purpose**: Deleted session cannot accept attendance

**Setup**:
- Token contains `session_id` for deleted session

**Expected**: `SessionNotFoundError` raised

---

### test_null_coordinates_rejected

**Purpose**: Missing GPS data rejected

**Setup**:
- Request with `latitude=null` or `longitude=null`

**Expected**: 400 Bad Request (serializer validation)

---

### test_zero_zero_coordinates_rejected

**Purpose**: Default/invalid GPS rejected

**Setup**:
- Request with `latitude=0`, `longitude=0`

**Expected**: `InvalidCoordinatesError` raised

**Why Important**: (0, 0) is in ocean, likely invalid default

---

### test_very_high_precision_coordinates

**Purpose**: Handle maximum decimal precision

**Setup**:
- Latitude with 8 decimals: `-1.28334567`
- Longitude with 8 decimals: `36.81667890`

**Expected**: Stored correctly without truncation

---

### test_concurrent_duplicate_attempts

**Purpose**: Race condition with database constraint

**Setup**:
- Two requests for same student/session at exact same time

**Expected**: One succeeds, one gets IntegrityError (mapped to 409)

**Why Important**: Database constraint is last line of defense

---

# PART 8: FIXTURES AND TEST DATA

## Test File

**File**: `tests/conftest.py`

**Purpose**: Reusable test data and setup

**Priority: MEDIUM** - Reduces test code duplication

---

## Fixtures

### sample_student_profile

**Purpose**: Create valid StudentProfile for testing

**Returns**: StudentProfile instance (BCS, Stream A)

---

### sample_session

**Purpose**: Create valid Session for testing

**Returns**: Session instance (active, with GPS coordinates)

---

### sample_attendance_data

**Purpose**: Dictionary with valid attendance fields

**Returns**:
```python
{
    "student_profile_id": 123,
    "session_id": 456,
    "latitude": Decimal("-1.28334000"),
    "longitude": Decimal("36.81667000"),
    "status": "present",
    "is_within_radius": True
}
```

---

### valid_token

**Purpose**: Generate valid JWT for testing

**Returns**: JWT string with required claims

---

### expired_token

**Purpose**: Generate expired JWT for testing

**Returns**: JWT string with `exp` in past

---

### mock_haversine_30m

**Purpose**: Mock location validator for 30m distance

**Returns**: Mock that returns `True` for `is_within_radius()`

---

### mock_haversine_50m

**Purpose**: Mock location validator for 50m distance (outside radius)

**Returns**: Mock that returns `False` for `is_within_radius()`

---

## Test Database Setup

**Django Test Database**:
- Separate test database created automatically
- Migrations applied before tests
- Database wiped after each test

**Why Important**: Isolated test environment

---

# TESTING SUMMARY

## Test Coverage Goals

| Component | Target Coverage | Priority |
|-----------|-----------------|----------|
| Models | 90%+ | HIGH |
| Repositories | 95%+ | CRITICAL |
| Services | 95%+ | CRITICAL |
| Handlers | 90%+ | HIGH |
| Integration | Key flows | CRITICAL |

---

## Critical Test Categories

**Priority: CRITICAL** - Must pass before deployment:
1. **Duplicate prevention** - `exists_for_student_and_session`
2. **QR code mismatch** - Fraud detection
3. **Token validation** - Expired, invalid, tampered
4. **Haversine distance** - GPS accuracy
5. **Unique constraint** - Database-level enforcement

**Priority: HIGH** - Important for robustness:
- Status determination logic
- Session validation (time windows)
- Eligibility checks (program/stream)
- Error response formatting

---

## Running Tests

**Command**: `pytest tests/attendance_recording/`

**With Coverage**: `pytest --cov=attendance_recording tests/attendance_recording/`

**Single Test**: `pytest tests/attendance_recording/test_services.py::test_verify_qr_matches_token_mismatch`

---

## Key Takeaways

1. **Three-factor verification testing** - Token, QR, GPS all validated
2. **Fraud detection critical** - QR mismatch must raise error and log
3. **Haversine accuracy** - Distance calculations verified with known values
4. **Duplicate prevention** - Tested at repository, service, and API levels
5. **Cross-context integration** - Token contract, session state, eligibility
6. **Edge cases** - Boundary conditions, GPS spoofing, race conditions
7. **Immutability** - No update operations allowed
8. **Security logging** - Fraud attempts recorded for audit

---

**Status**: 📋 Complete testing specification ready for implementation

**Test Count Estimate**: 70+ test cases across 6 parts + fixtures