# models_guide.md

Brief: Complete specification for EmailNotification model. Defines notification lifecycle, JWT token storage, status tracking, and delivery timestamps. Focuses on maintaining audit trail and enabling reliable async delivery.

---

## Model Overview

**Purpose**: Track email notifications sent to students when sessions are created. Each record represents one email to one student for one session, with embedded JWT token for secure attendance marking.

**Why It Matters**: 
- Provides audit trail (who was notified, when, success/failure)
- Enables async processing (create record immediately, send later)
- Supports retry logic for failed deliveries
- Prevents duplicate notifications via unique constraint

---

# EMAILNOTIFICATION MODEL

## Field Specifications

### Primary Key
- **email_id**: Integer, auto-increment
  - Purpose: Unique identifier for each notification
  - Why: Simple sequential ID for logging and debugging

### Foreign Keys (Cross-Context References)

**Priority: CRITICAL** - These link notifications to sessions and students

- **session**: ForeignKey → Session (Session Management Context)
  - Relationship: Many notifications per session (one per eligible student)
  - On delete: **CASCADE** (delete notifications when session deleted)
  - Why CASCADE: Notifications have no meaning without the session
  - Nullable: **No** (every notification must reference a session)
  - Access pattern: `session.email_notifications.all()` → all emails for a session

- **student_profile**: ForeignKey → StudentProfile (User Management Context)
  - Relationship: Many notifications per student (across different sessions)
  - On delete: **CASCADE** (delete notifications when student removed)
  - Why CASCADE: GDPR compliance, no orphaned notifications
  - Nullable: **No** (every notification has a recipient)
  - Access pattern: `student_profile.email_notifications.all()` → student's email history

### Token Fields

**Priority: CRITICAL** - Enable secure attendance marking

- **token**: TextField/CharField (length ~200-500)
  - Purpose: Store JWT token for secure attendance link
  - Content: Encoded JWT string (e.g., `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`)
  - Why stored: Needed for validation, audit, and debugging
  - Nullable: **No** (every notification must have a token)
  - Security: Token is signed, cannot be forged, single-use
  - Index: **Yes** (fast lookup during attendance marking)

- **token_expires_at**: DateTimeField with timezone
  - Purpose: Token expiration timestamp
  - Why separate from JWT `exp`: Enables DB queries for expired tokens
  - Validation: Must be future time when created (CHECK constraint)
  - Typical value: Session start time + 30-60 minutes
  - Use case: Query and cleanup expired tokens, enforce time limits
  - Nullable: **No**

### Status Tracking

**Priority: HIGH** - Enables retry logic and monitoring

- **status**: CharField with choices, max_length=20
  - Purpose: Track email delivery state
  - **Choices**: 
    - `pending`: Created, queued, not yet sent
    - `sent`: Successfully delivered to SMTP server
    - `failed`: Delivery attempt failed
  - Default: `pending`
  - Why important: 
    - Drives background worker (query `status='pending'`)
    - Enables admin to identify failures
    - Supports retry workflow (`failed` → `pending`)
  - Nullable: **No**
  - Index: **Yes** (frequent queries by status)

### Timestamps

**Priority: HIGH** - Audit trail and debugging

- **created_at**: DateTimeField, auto_now_add=True
  - Purpose: When notification was created/queued
  - Why: Audit trail, measure time-to-send
  - Nullable: **No** (auto-set)

- **sent_at**: DateTimeField, **NULLABLE**
  - Purpose: When email was successfully sent
  - Why nullable: 
    - `NULL` when status is `pending` or `failed`
    - Set when status becomes `sent`
  - Use case: Calculate delivery time, filter recently sent
  - Important: Only set when `status = sent`

## Database Constraints

**Priority: CRITICAL** - Data integrity and uniqueness

### Unique Constraint
```
UNIQUE (session_id, student_profile_id)
```
- **Why**: Prevent duplicate emails to same student for same session
- **Example**: Student A cannot receive 2 emails for Session 123
- **Enforcement**: Database raises IntegrityError on duplicate insert

### Check Constraints
```
CHECK (status IN ('pending', 'sent', 'failed'))
```
- **Why**: Only allow valid status values

```
CHECK (token_expires_at > created_at)
```
- **Why**: Token expiry must be in future when created

### Cascade Rules
- Session deleted → Cascade delete notifications
- Student deleted → Cascade delete notifications
- **Why**: Maintain referential integrity, no orphaned records

## Indexes

**Priority: HIGH** - Query performance

- **Index on session_id**: Fast lookup of all emails for a session
  - Query: "Show all notifications for Session 123"
  
- **Index on student_profile_id**: Fast lookup of student's notification history
  - Query: "Show all emails sent to Student A"
  
- **Index on status**: Fast lookup of pending/failed emails
  - Query: "Find all pending emails to send"
  
- **Index on token**: Fast validation during attendance marking
  - Query: "Find notification by token ABC..."

## Model Methods and Properties

**Purpose**: Encapsulate business logic and derived values

### is_expired()
- **Returns**: Boolean
- **Logic**: `now() > token_expires_at`
- **Use case**: Check if token is still valid before attendance marking

### is_sent()
- **Returns**: Boolean
- **Logic**: `status == 'sent'`
- **Use case**: Quick status check

### can_retry()
- **Returns**: Boolean
- **Logic**: `status == 'failed'`
- **Use case**: Admin retry workflow

### mark_as_sent(sent_timestamp)
- **Purpose**: Update status to sent and set sent_at
- **Why method**: Ensures consistency (both fields updated together)
- **Validation**: Only allow if status is `pending`

### mark_as_failed()
- **Purpose**: Update status to failed, keep sent_at NULL
- **Why method**: Atomic status change

## File Organization

**Priority: MEDIUM** - Maintainability

```
email_notifications/
├── models.py                    # EmailNotification model
├── repositories/                # Separate folder for data access
│   └── email_repository.py      # EmailNotificationRepository
├── services/                    # Business logic
│   ├── jwt_service.py           # Token generation/validation
│   ├── email_service.py         # SMTP sending
│   └── notification_service.py  # Orchestration
├── tasks.py                     # Celery background tasks
├── views.py                     # API endpoints
├── serializers.py               # Django REST Framework
├── urls.py                      # Routing
└── tests/
    ├── test_models.py
    ├── test_repositories.py
    ├── test_services.py
    └── fixtures.py
```

**Why this structure**:
- Separation of concerns (models ≠ logic)
- Services folder enables multiple service classes
- Repositories isolate database queries
- Easy to mock services in tests

## Validation Rules

**Priority: HIGH** - Enforced in services, not models

### At Creation Time
1. **Session must exist and be valid**
   - Session not in past (optional business rule)
   - Session has eligible students

2. **Student must be eligible**
   - Student is active (`is_active=True`)
   - Student belongs to session's program/stream

3. **Token expiry must be reasonable**
   - Typically: session.time_created + 30-60 minutes
   - Must be future time

### Status Transition Rules
- `pending` → `sent`: ✅ Allowed (normal flow)
- `pending` → `failed`: ✅ Allowed (delivery error)
- `sent` → any: ❌ **NOT allowed** (sent is final)
- `failed` → `pending`: ✅ Allowed (retry)

**Why these rules**: 
- Once sent, cannot unsend
- Failed emails can be retried
- Prevents invalid state transitions

## Example Data Scenarios

### Scenario 1: Successful Delivery
```
EmailNotification:
- email_id: 501
- session_id: 123 (CS201 Lecture on 2025-10-25)
- student_profile_id: 789 (John Doe)
- token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdHVkZW50X3Byb2ZpbGVfaWQiOjc4OSwic2Vzc2lvbl9pZCI6MTIzLCJleHAiOjE3MjkzNDEwMDB9.abc123"
- token_expires_at: 2025-10-25 09:00:00 (session start + 1 hour)
- status: "sent"
- created_at: 2025-10-25 07:00:00 (when session created)
- sent_at: 2025-10-25 07:02:15 (2 minutes later)
```

### Scenario 2: Failed Delivery (Invalid Email)
```
EmailNotification:
- email_id: 502
- session_id: 123
- student_profile_id: 790 (Alice Brown)
- token: "eyJ..."
- token_expires_at: 2025-10-25 09:00:00
- status: "failed"
- created_at: 2025-10-25 07:00:00
- sent_at: NULL (never sent)

Error log: "SMTP Error: Invalid recipient address"
```

### Scenario 3: Pending (Not Yet Sent)
```
EmailNotification:
- email_id: 503
- session_id: 124
- student_profile_id: 791 (Bob Wilson)
- token: "eyJ..."
- token_expires_at: 2025-10-25 15:00:00
- status: "pending"
- created_at: 2025-10-25 14:00:00
- sent_at: NULL (waiting for background worker)
```

## Migration Considerations

**Priority: HIGH** - Database setup

### Initial Migration
```python
# Pseudo-migration steps
operations = [
    CreateModel(
        name='EmailNotification',
        fields=[
            ('email_id', AutoField(primary_key=True)),
            ('session', ForeignKey(..., on_delete=CASCADE)),
            ('student_profile', ForeignKey(..., on_delete=CASCADE)),
            ('token', TextField()),
            ('token_expires_at', DateTimeField()),
            ('status', CharField(max_length=20, choices=[...])),
            ('created_at', DateTimeField(auto_now_add=True)),
            ('sent_at', DateTimeField(null=True, blank=True)),
        ],
    ),
    AddConstraint(
        model_name='emailnotification',
        constraint=UniqueConstraint(
            fields=['session', 'student_profile'],
            name='unique_email_per_student_session'
        ),
    ),
    AddIndex(model_name='emailnotification', index=Index(fields=['session'])),
    AddIndex(model_name='emailnotification', index=Index(fields=['student_profile'])),
    AddIndex(model_name='emailnotification', index=Index(fields=['status'])),
    AddIndex(model_name='emailnotification', index=Index(fields=['token'])),
]
```

### Why Nullable Fields Matter
- **sent_at is NULLABLE**: Critical for distinguishing pending/failed from sent
- **All other fields NOT NULL**: Required for notification to be meaningful

## Common Query Patterns

**Priority: HIGH** - Optimize these queries

```
# Get pending emails (for background worker)
SELECT * FROM email_notifications 
WHERE status = 'pending' 
ORDER BY created_at ASC
LIMIT 100;

# Get all emails for a session
SELECT * FROM email_notifications 
WHERE session_id = 123;

# Get failed emails (for admin retry)
SELECT * FROM email_notifications 
WHERE status = 'failed';

# Find notification by token (during attendance)
SELECT * FROM email_notifications 
WHERE token = 'eyJ...' 
LIMIT 1;

# Get student's notification history
SELECT * FROM email_notifications 
WHERE student_profile_id = 789 
ORDER BY created_at DESC;

# Count sent vs pending vs failed
SELECT status, COUNT(*) 
FROM email_notifications 
GROUP BY status;
```

---

**Status**: 📋 Complete model specification ready for implementation

**Key Takeaways**:
1. **One email per student per session** (unique constraint)
2. **Status drives workflow** (pending → sent/failed)
3. **sent_at nullable** (only set when sent)
4. **Indexes on session, student, status, token** (performance)
5. **CASCADE deletes** (maintain referential integrity)