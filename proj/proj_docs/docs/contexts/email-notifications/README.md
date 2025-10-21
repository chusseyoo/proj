# README.md

Brief: Overview and implementation manual for Email Notifications context. Scope, entities, business rules, integration points.

# Email Notifications Bounded Context

## Purpose

This bounded context handles email notification generation and delivery when sessions are created. It generates JWT tokens for secure attendance links and manages email delivery status.

## Scope

### What This Context Handles
- Email notification generation for eligible students
- JWT token generation (time-limited, single-use)
- Email queuing and delivery
- Email delivery status tracking (pending, sent, failed)
- Token expiry management

### What This Context Does NOT Handle
- Session creation → handled by Session Management Context
- Student eligibility determination → uses data from Session Management Context
- Attendance marking → handled by Attendance Recording Context
- Token validation during attendance → handled by Attendance Recording Context
- User email addresses → retrieved from User Management Context

## Core Entities

### EmailNotification
- **Primary entity** representing an email notification sent to a student for a session
- Attributes:
  - `email_id` (Primary Key, Integer, Auto-increment) - Unique identifier
  - `session_id` (Foreign Key → Session.session_id, NOT NULL) - Session this email is for
  - `student_profile_id` (Foreign Key → StudentProfile.student_profile_id, NOT NULL) - Recipient student
  - `token` (String, NOT NULL) - JWT token for attendance link
  - `token_expires_at` (DateTime, NOT NULL) - Token expiration timestamp
  - `status` (Enum, NOT NULL) - Delivery status: `pending`, `sent`, `failed`
  - `created_at` (DateTime, NOT NULL, Auto-set) - When notification was created/queued
  - `sent_at` (DateTime, **NULLABLE**) - When email was successfully sent
    - **NULL if not yet sent** (`status = pending` or `failed`)
    - **Set when sent** (`status = sent`)

**Important Notes:**
- One email per student per session (enforced by UNIQUE constraint)
- JWT token embedded in email link (e.g., `https://app.com/attendance?token=...`)
- Token is short-lived (typically 30-60 minutes)
- Recipient email address is NOT stored (fetched from User.email at send time)
- Email body/subject are NOT stored (generated dynamically)

## Business Rules

### Email Generation Workflow

When a session is created, the Email Notification Context:

1. **Receives session creation event** from Session Management Context
2. **Identifies eligible students**:
   - Query students by `program_id` and `stream_id` (from session)
   - Filter only active students (`is_active = True`)
3. **For each eligible student**:
   - Generate JWT token with payload: `{student_profile_id, session_id, exp}`
   - Create EmailNotification record with status = `pending`
   - Set `token_expires_at` (e.g., session start time + 60 minutes)
4. **Queue emails** for background worker to send

### JWT Token Structure

**Payload**:
```json
{
  "student_profile_id": 123,
  "session_id": 456,
  "iat": 1729339200,
  "exp": 1729341000
}
```

**Properties**:
- **Secret**: Server-side secret key (environment variable)
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Expiry**: Typically 30-60 minutes from session start
- **Single-use**: Token becomes invalid after attendance is marked

**Important Notes:**
- Token does NOT contain sensitive data (no email, name, password)
- Token is signed and cannot be forged
- Token expiry is enforced both in JWT and `token_expires_at` field
- Expired tokens are rejected during attendance marking

### Email Delivery Status

1. **pending**:
   - Email created but not yet sent
   - Queued for background worker
   - `sent_at` is NULL

2. **sent**:
   - Email successfully delivered to SMTP server
   - `sent_at` is set to delivery timestamp
   - Does NOT guarantee student received it (that's email provider's responsibility)

3. **failed**:
   - Email delivery failed (SMTP error, invalid email, etc.)
   - `sent_at` remains NULL
   - Can be retried manually by admin

**Important Notes:**
- Status is optimistic (assumes delivery from SMTP server to inbox)
- No tracking for email opens or link clicks (minimal tracking by design)
- Failed emails should be logged for admin review

### Email Content

Email is generated dynamically (not stored in database):

**Subject**:
```
Attendance Session Created: [Course Name]
```

**Body** (plain text example):
```
Hi [Student First Name],

Your lecturer has created an attendance session for:

Course: [Course Name] ([Course Code])
Date: [Session Date]
Time: [Start Time] - [End Time]

Click the link below to mark your attendance:
[Attendance Link with Token]

This link will expire at [Token Expiry Time].

Important:
- You must scan your student ID QR code
- You must be within 30 meters of the session location

Thanks,
Attendance Management System
```

**Attendance Link**:
```
https://yourdomain.com/attendance?token=eyJhbGc...
```

## Validation Rules

### Token Generation
- Must include `student_profile_id`, `session_id`, `exp`
- Expiry must be in the future
- Token must be properly signed with secret key

### Email Notification Creation
- `session_id` must exist
- `student_profile_id` must exist and be active
- One notification per student per session (UNIQUE constraint)
- `token_expires_at` must be after current time

### Status Transitions
- `pending` → `sent`: Allowed
- `pending` → `failed`: Allowed
- `sent` → Any: NOT allowed (cannot revert sent status)
- `failed` → `pending`: Allowed (retry)

## Database Constraints

### EmailNotification Table
```sql
CREATE TABLE email_notifications (
  email_id SERIAL PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  student_profile_id INTEGER NOT NULL REFERENCES student_profiles(student_profile_id) ON DELETE CASCADE,
  token TEXT NOT NULL,
  token_expires_at TIMESTAMPTZ NOT NULL,
  status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'sent', 'failed')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  sent_at TIMESTAMPTZ,  -- NULLABLE
  
  CONSTRAINT unique_email_per_student_session UNIQUE(session_id, student_profile_id),
  CONSTRAINT token_expiry_future CHECK (token_expires_at > created_at)
);

CREATE INDEX idx_email_notifications_session_id ON email_notifications(session_id);
CREATE INDEX idx_email_notifications_student_id ON email_notifications(student_profile_id);
CREATE INDEX idx_email_notifications_status ON email_notifications(status);
CREATE INDEX idx_email_notifications_token ON email_notifications(token);
```

**Important Constraint Notes:**
- `ON DELETE CASCADE`: Deleting session or student deletes notifications
- `UNIQUE(session_id, student_profile_id)`: One email per student per session
- `CHECK` constraint on status: Only allowed values
- `sent_at` is nullable (NULL until sent)
- Index on `token` for fast lookup during attendance marking
- Index on `status` for querying pending/failed emails

## Django Implementation Structure

```
email_notifications/
├── models.py           # EmailNotification model
├── repositories.py     # EmailNotificationRepository
├── services.py         # EmailService, JWTTokenService
├── handlers.py         # GenerateEmailNotificationsHandler
├── tasks.py           # Celery/background tasks for sending emails
├── views.py           # API endpoints (minimal - mostly internal)
├── serializers.py     # Request/response serialization
├── validators.py      # Token validation, email validation
├── permissions.py     # AdminOnly for manual retry
├── urls.py            # URL routing
├── tests/             # Unit and integration tests
└── migrations/        # Database migrations
```

## Integration Points

### Outbound Dependencies (What We Call)
- **Infrastructure**: 
  - SMTP server for email delivery
  - JWT library (PyJWT) for token generation
  - Background task queue (Celery/Redis)
  
- **User Management Context**: 
  - Get student email addresses (User.email via StudentProfile.user_id)
  - Get student names for email personalization
  
- **Academic Structure Context**: 
  - Get course name and code for email content
  
- **Session Management Context**: 
  - Get session details (date, time, location) for email content

### Inbound Dependencies (Who Calls Us)
- **Session Management Context**: 
  - Trigger email generation when session is created
  - Pass session_id and eligible student criteria
  
- **Attendance Recording Context**: 
  - Validate token during attendance marking
  - Extract student_profile_id and session_id from token
  - Check token expiry

## Background Processing

Email sending is asynchronous to avoid blocking session creation:

1. **Session created** → EmailNotification records created instantly (status = pending)
2. **Background worker** (Celery task):
   - Queries pending emails (`status = pending`)
   - For each email:
     - Fetch student email from User table
     - Fetch session/course details
     - Generate email content
     - Send via SMTP
     - Update status to `sent` and set `sent_at`
     - On failure: Update status to `failed`
3. **Retries**: Failed emails can be retried manually or automatically

## Files in This Context

### 1. `README.md` (this file)
Overview of the bounded context

### 2. `models_guide.md`
Step-by-step guide for creating Django models:
- EmailNotification model
- Status enum field
- Nullable sent_at field
- UNIQUE constraint

### 3. `repositories_guide.md`
Guide for creating repository layer:
- EmailNotificationRepository
- Query pending emails
- Query by session, by student
- Update status

### 4. `services_guide.md`
Guide for creating domain services:
- JWTTokenService (generate, verify, decode)
- EmailService (send email via SMTP)
- NotificationGenerationService (create notifications for eligible students)

### 5. `handlers_guide.md`
Guide for creating application layer handlers:
- GenerateEmailNotificationsHandler (triggered by session creation)
- RetryFailedEmailHandler (admin can retry failed emails)

### 6. `tasks_guide.md`
Guide for creating background tasks:
- SendPendingEmailsTask (Celery task)
- Process email queue
- Handle SMTP errors
- Update status

### 7. `views_guide.md`
Guide for creating API endpoints:
- POST /api/v1/admin/emails/retry/ (retry failed emails)
- GET /api/v1/sessions/{id}/emails/ (list emails for session)
- Internal API: POST /api/v1/internal/emails/generate/ (called by Session Management)

### 8. `testing_guide.md`
Guide for writing tests:
- Test JWT token generation and validation
- Test email notification creation for eligible students
- Test status transitions
- Test SMTP sending (mocked)
- Test background task processing

## Implementation Order

1. **Models** (`models_guide.md`) - EmailNotification model
2. **Repositories** (`repositories_guide.md`) - Data access
3. **Services** (`services_guide.md`) - JWT + Email services
4. **Handlers** (`handlers_guide.md`) - Generation handler
5. **Tasks** (`tasks_guide.md`) - Background email sending
6. **Views** (`views_guide.md`) - Admin retry endpoint
7. **Tests** (`testing_guide.md`) - Comprehensive testing

## Next Steps

After reading this overview:
1. Understand JWT token structure and payload
2. Verify email status lifecycle (pending → sent/failed)
3. Confirm nullable sent_at field
4. Understand background processing flow
5. Review integration with Session Management (trigger)
6. Review integration with Attendance Recording (token validation)
7. Proceed to detailed guide files

---

**Status**: 📝 Overview Complete - Ready for detailed guide creation
