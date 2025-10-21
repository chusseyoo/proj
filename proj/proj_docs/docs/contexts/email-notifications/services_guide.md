# services_guide.md

Brief: Complete service layer specification for Email Notifications. Three focused services: JWTTokenService (token lifecycle), EmailSenderService (SMTP delivery), NotificationGenerationService (orchestration). Each service has single responsibility with brief explanations of business rules and integration points.

---

## Service Layer Purpose

**Why Services Matter**:
- **Business logic lives here**: Validation, authorization, workflow orchestration
- **Thin repositories**: Data access only, no logic
- **Testability**: Mock repositories and external dependencies (SMTP, User Management)
- **Reusability**: Services called by handlers, API views, background tasks

---

# PART 1: JWTTOKENSERVICE

## Overview

**File**: `services/jwt_service.py`

**Purpose**: Generate, validate, and decode JWT tokens for secure attendance links

**Why Separate Service**: 
- Token logic is complex (signing, validation, expiry)
- Reused in multiple contexts (generation, validation during attendance)
- Easy to swap JWT library or algorithm

**Dependencies**:
- PyJWT library (`import jwt`)
- Secret key from environment/settings (`settings.JWT_SECRET_KEY`)
- Token expiry configuration (`settings.TOKEN_EXPIRY_MINUTES`, default 60)

---

## Method Specifications

### generate_token(student_profile_id: int, session_id: int, expires_at: datetime) → str

**Purpose**: Create JWT token for attendance link

**Why Important**: Token securely identifies student and session without exposing sensitive data

**Input Parameters**:
- `student_profile_id`: Student's profile ID (not user_id, to avoid cross-context leakage)
- `session_id`: Session this token is for
- `expires_at`: Token expiration timestamp (typically session start + 60 mins)

**Token Payload**:
```json
{
  "student_profile_id": 123,
  "session_id": 456,
  "iat": 1729339200,       // issued at (Unix timestamp)
  "exp": 1729342800        // expires at (Unix timestamp)
}
```

**Why These Fields**:
- `student_profile_id`: Identifies recipient
- `session_id`: Identifies session
- `iat`: Audit trail (when token created)
- `exp`: Automatic expiry enforcement by JWT library

**Signing**:
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Why HS256**: Symmetric key, simpler than RSA, sufficient for server-side validation
- **Secret**: Environment variable, never in code or database
- **Output**: Encoded string like `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

**Returns**: JWT token string (200-500 characters)

**Error Handling**:
- Invalid `expires_at` (past time) → Raise `InvalidTokenExpiryError`
- Missing secret key → Raise `ConfigurationError`

---

### validate_token(token: str) → bool

**Purpose**: Check if token is valid (signature and expiry)

**Why Important**: First line of defense during attendance marking

**Validation Steps**:
1. **Signature verification**: Ensure token not tampered with
2. **Expiry check**: Token not expired (`exp` < now)
3. **Format check**: Token structure valid (header.payload.signature)

**Returns**: 
- `True` if valid
- `False` if invalid, expired, or malformed

**Why Boolean**: Simple yes/no for quick checks; use `decode_token` for detailed validation

**Note**: Does NOT check if token already used (single-use enforcement in Attendance Recording context)

---

### decode_token(token: str) → dict

**Purpose**: Extract payload from valid token

**Why Important**: Get `student_profile_id` and `session_id` for attendance marking

**Returns**: Dictionary with payload:
```python
{
  "student_profile_id": 123,
  "session_id": 456,
  "iat": 1729339200,
  "exp": 1729342800
}
```

**Error Handling**:
- **Invalid signature** → Raise `InvalidTokenError` ("Token has been tampered with")
- **Expired token** → Raise `ExpiredTokenError` ("Token has expired")
- **Malformed token** → Raise `InvalidTokenError` ("Token format invalid")

**Use Case**: Attendance Recording service calls this to extract student and session IDs

---

### is_token_expired(token: str) → bool

**Purpose**: Check expiry without full validation

**Why Useful**: Distinguish between "expired" and "invalid signature" for better error messages

**Returns**: `True` if expired, `False` if not (or if token invalid)

**Implementation**: Try to decode and catch `ExpiredTokenError`

---

## Security Considerations

**Priority: CRITICAL**

1. **Secret Key Protection**:
   - Store in environment variable (`JWT_SECRET_KEY`)
   - Never commit to version control
   - Rotate periodically (invalidates old tokens)

2. **Algorithm Choice**:
   - Use HS256 (symmetric)
   - Never use "none" algorithm (security vulnerability)

3. **Token Expiry**:
   - Short-lived (30-60 minutes)
   - Balance: too short = student misses window; too long = security risk

4. **Single-Use Enforcement**:
   - JWT doesn't track usage
   - Attendance Recording context marks token as used in database

---

# PART 2: EMAILSENDERSERVICE

## Overview

**File**: `services/email_sender_service.py`

**Purpose**: Send emails via SMTP with configurable templates

**Why Separate Service**:
- SMTP logic complex (connection, authentication, retries)
- Easy to mock in tests (no actual emails sent)
- Can swap email backend (SMTP → SendGrid → AWS SES)

**Dependencies**:
- Django email backend (`django.core.mail.send_mail`)
- SMTP settings (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`)
- Email templates (plain text and HTML)

---

## Method Specifications

### send_attendance_notification(recipient_email: str, context: dict) → bool

**Purpose**: Send attendance notification email to student

**Why Important**: Core delivery mechanism; must handle SMTP errors gracefully

**Input Parameters**:
- `recipient_email`: Student's email address (from `User.email`)
- `context`: Dictionary with template variables:
  ```python
  {
    "student_first_name": "John",
    "course_name": "Data Structures",
    "course_code": "CS201",
    "session_date": "2025-10-25",
    "start_time": "08:00",
    "end_time": "10:00",
    "attendance_link": "https://app.com/attendance?token=eyJ...",
    "token_expiry": "2025-10-25 09:00"
  }
  ```

**Email Structure**:
- **Subject**: `"Attendance Session Created: {course_name}"`
- **From**: System email (`no-reply@yourdomain.com`)
- **To**: `recipient_email`
- **Body**: Plain text template with link
- **Optional HTML**: Rich HTML template (recommended for styling)

**Email Template Example** (Plain Text):
```
Hi {student_first_name},

Your lecturer has created an attendance session for:

Course: {course_name} ({course_code})
Date: {session_date}
Time: {start_time} - {end_time}

Click the link below to mark your attendance:
{attendance_link}

This link will expire at {token_expiry}.

Important:
- You must scan your student ID QR code
- You must be within 30 meters of the session location

Thanks,
Attendance Management System
```

**Returns**: 
- `True` if email sent successfully
- `False` if delivery failed (SMTP error, invalid email, etc.)

**Error Handling**:
- **SMTP errors**: Log error, return False (do not raise exception)
- **Invalid recipient**: Log warning, return False
- **Connection timeout**: Retry once, then return False

**Why Boolean Return**: Allows caller to update status (sent/failed) based on result

---

### send_bulk_emails(emails: List[dict]) → dict

**Purpose**: Send multiple emails efficiently

**Why Important**: Session with 200 students needs bulk sending

**Input**: List of email dictionaries:
```python
[
  {
    "recipient_email": "john@example.com",
    "context": {...}
  },
  {
    "recipient_email": "alice@example.com",
    "context": {...}
  },
  ...
]
```

**Returns**: Summary dictionary:
```python
{
  "total": 200,
  "sent": 195,
  "failed": 5,
  "failed_emails": ["invalid@example.com", ...]
}
```

**Implementation Strategy**:
- Use SMTP connection pooling (single connection for all emails)
- Batch emails (e.g., 50 per connection to avoid timeout)
- Continue on individual failures (don't stop entire batch)

**Why Bulk Method**: 
- Reuse SMTP connection (faster)
- Better error handling (partial failures OK)

---

## Email Template Management

**Priority: MEDIUM** - Maintainability and customization

### Template Location
```
email_notifications/
├── templates/
│   └── emails/
│       ├── attendance_notification.txt      # Plain text
│       └── attendance_notification.html     # HTML (optional)
```

**Why Separate Templates**:
- Easy to customize without changing code
- Support for plain text + HTML multipart emails
- Translatable (future i18n support)

### Template Variables
All templates receive `context` dictionary with:
- Student info: `student_first_name`
- Course info: `course_name`, `course_code`
- Session info: `session_date`, `start_time`, `end_time`
- Link: `attendance_link` (with embedded token)
- Expiry: `token_expiry`

---

# PART 3: NOTIFICATIONGENERATIONSERVICE

## Overview

**File**: `services/notification_generation_service.py`

**Purpose**: Orchestrate notification creation for eligible students when session created

**Why Separate Service**: 
- Complex workflow (eligibility → token generation → bulk creation)
- Integrates multiple services (JWTTokenService, EmailNotificationRepository)
- Cross-context integration (User Management, Session Management)

**Dependencies**:
- `EmailNotificationRepository` (create notifications)
- `JWTTokenService` (generate tokens)
- `SessionRepository` (get session details) - from Session Management context
- `StudentProfileRepository` (get eligible students) - from User Management context

---

## Method Specifications

### generate_notifications_for_session(session_id: int) → dict

**Purpose**: Create EmailNotification records for all eligible students in a session

**Why Critical**: Triggered immediately when session created; must be fast and reliable

**Workflow Steps**:

1. **Get Session Details**
   - Fetch session from database
   - Extract: `program_id`, `stream_id`, `time_created`, `time_ended`
   - Validate session exists
   - **Why**: Need targeting info (program/stream) and timing for token expiry

2. **Determine Eligible Students**
   - If `stream_id` is NULL: All students in `program_id`
   - If `stream_id` is set: Only students in that stream
   - Filter: `is_active = True` (exclude inactive students)
   - **Why**: Only active, enrolled students should receive notifications
   - **Cross-context call**: User Management context provides eligibility logic

3. **Calculate Token Expiry**
   - Formula: `session.time_created + TOKEN_EXPIRY_MINUTES` (e.g., + 60 mins)
   - **Why**: Token valid from session start until expiry window
   - **Business Rule**: Expiry should be after session ends (give students buffer time)

4. **Generate Notifications (Bulk)**
   ```python
   notifications = []
   for student in eligible_students:
       token = jwt_service.generate_token(
           student_profile_id=student.student_profile_id,
           session_id=session_id,
           expires_at=token_expiry
       )
       notifications.append({
           "session_id": session_id,
           "student_profile_id": student.student_profile_id,
           "token": token,
           "token_expires_at": token_expiry,
           "status": "pending"
       })
   ```
   - **Why Loop**: Each student needs unique token
   - **Why Bulk**: 200 students = 200 tokens, but single DB insert

5. **Save to Database**
   ```python
   created = repository.bulk_create(notifications)
   ```
   - **Performance**: 1 transaction vs 200 individual inserts
   - **Why Pending Status**: Background worker will send later

6. **Return Summary**
   ```python
   return {
       "session_id": session_id,
       "notifications_created": len(created),
       "eligible_students": len(eligible_students)
   }
   ```

**Returns**: Summary dictionary with counts

**Error Handling**:
- Session not found → Raise `SessionNotFoundError`
- No eligible students → Return success with 0 created (not an error)
- Duplicate notification → Skip (unique constraint handles this)
- Token generation failure → Raise `TokenGenerationError`

**Performance Considerations**:
- **Critical**: Use `bulk_create` (10-50x faster for large batches)
- **Optional**: Run in background task if >500 students (rare)

---

### retry_failed_notifications(email_ids: List[int]) → dict

**Purpose**: Reset failed notifications to pending for retry

**Why Important**: Admin tool to recover from temporary SMTP outages

**Workflow**:
1. Query notifications by IDs
2. Validate: `status = 'failed'`
3. Update: `status = 'pending'`, `sent_at = NULL`
4. Background worker picks them up next run

**Returns**:
```python
{
  "retried": 8,
  "skipped": 2,  # Already sent or not failed
  "errors": ["Notification 123 not found"]
}
```

**Authorization**: Admin only (enforce in API layer)

---

## Integration Points

**Priority: HIGH** - Cross-context dependencies

### Session Management Context
- **What we need**: Session details (program, stream, time window)
- **How**: `SessionRepository.get_by_id(session_id)`
- **Why**: Determine eligible students and token expiry

### User Management Context
- **What we need**: Eligible students (profile IDs and emails)
- **How**: `StudentProfileRepository.get_by_program_and_stream(program_id, stream_id, active_only=True)`
- **Why**: Know who to send notifications to
- **Email retrieval**: `User.email` via `StudentProfile.user`

### Academic Structure Context (Indirect)
- **What we need**: Course name/code for email template
- **How**: Through session relationship (`session.course.course_name`)
- **Why**: Personalize email content

---

## Service Collaboration Pattern

**How services work together**:

```
NotificationGenerationService (orchestrator)
    ↓ calls
JWTTokenService.generate_token() (200 times)
    ↓ uses tokens to build
EmailNotificationRepository.bulk_create()
    ↓ creates records with status=pending
    
Later (background task):
    ↓ queries
EmailNotificationRepository.get_pending_emails()
    ↓ for each notification
EmailSenderService.send_attendance_notification()
    ↓ updates
EmailNotificationRepository.update_status()
```

**Why This Pattern**:
- Each service has single responsibility
- Easy to test in isolation (mock dependencies)
- Clear separation of concerns

---

## File Organization

**Priority: MEDIUM** - Maintainability

```
email_notifications/
├── services/
│   ├── __init__.py
│   ├── jwt_service.py                      # JWTTokenService
│   ├── email_sender_service.py             # EmailSenderService
│   └── notification_generation_service.py  # NotificationGenerationService
├── repositories/
│   └── email_repository.py
├── tasks.py                                 # Celery background tasks
├── templates/
│   └── emails/
│       ├── attendance_notification.txt
│       └── attendance_notification.html
└── tests/
    ├── test_jwt_service.py
    ├── test_email_sender_service.py
    └── test_notification_generation_service.py
```

**Why Three Separate Service Files**:
- Clear separation of concerns
- Easy to locate specific logic
- Each file <300 lines (maintainable size)

---

## Error Handling and Domain Exceptions

**Priority: HIGH** - Consistent error semantics

### Custom Exceptions

```python
# email_notifications/exceptions.py

class EmailNotificationError(Exception):
    """Base exception"""
    pass

class InvalidTokenError(EmailNotificationError):
    """Token signature invalid or malformed"""
    pass

class ExpiredTokenError(EmailNotificationError):
    """Token has expired"""
    pass

class InvalidTokenExpiryError(EmailNotificationError):
    """Token expiry time is invalid (e.g., in the past)"""
    pass

class SessionNotFoundError(EmailNotificationError):
    """Session does not exist"""
    pass

class TokenGenerationError(EmailNotificationError):
    """Failed to generate JWT token"""
    pass

class EmailDeliveryError(EmailNotificationError):
    """SMTP delivery failed"""
    pass
```

### Error Mapping to HTTP Status

Services raise domain exceptions → API layer maps to HTTP:
- `SessionNotFoundError` → 404 Not Found
- `InvalidTokenError` → 400 Bad Request
- `ExpiredTokenError` → 410 Gone
- `TokenGenerationError` → 500 Internal Server Error
- `EmailDeliveryError` → 502 Bad Gateway

**Why Domain Exceptions**: Services don't know about HTTP; stay technology-agnostic

---

## Service Summary

### JWTTokenService (Token Lifecycle)
- `generate_token` - Create JWT for student and session
- `validate_token` - Check signature and expiry
- `decode_token` - Extract payload
- `is_token_expired` - Specific expiry check

### EmailSenderService (SMTP Delivery)
- `send_attendance_notification` - Send single email
- `send_bulk_emails` - Send multiple emails efficiently

### NotificationGenerationService (Orchestration)
- `generate_notifications_for_session` - Create notifications for all eligible students
- `retry_failed_notifications` - Admin retry workflow

---

**Status**: 📋 Complete service specification ready for implementation

**Key Takeaways**:
1. **Three focused services** (JWT, Email, Orchestration)
2. **Single responsibility** per service
3. **Bulk operations for efficiency** (bulk_create, bulk_send)
4. **Token security** (HS256, secret key, short expiry)
5. **Async delivery** (create pending, send later)