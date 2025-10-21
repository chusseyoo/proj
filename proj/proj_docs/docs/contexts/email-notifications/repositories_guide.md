# repositories_guide.md

Brief: Complete repository layer specification for Email Notifications. Encapsulates all database operations with focus on status-based queries, bulk creation for efficiency, and token lookup for attendance validation.

---

## Repository Purpose

**Why Repositories Matter**:
- **Separation of concerns**: Services focus on business logic, repositories handle data access
- **Testability**: Easy to mock repositories in service tests
- **Query optimization**: Centralize complex queries and indexing strategies
- **Consistency**: Single source of truth for data access patterns

---

# EMAILNOTIFICATIONREPOSITORY

## Overview

**File Location**: `repositories/email_repository.py`

**Responsibilities**:
- CRUD operations for EmailNotification
- Status-based queries (pending, sent, failed)
- Bulk creation for efficiency (one session → many students)
- Token lookup for attendance validation
- Session/student filtering

**Dependencies**:
- EmailNotification model
- Django ORM QuerySet API

**Why Separate File**: 
- Keeps `models.py` clean (only model definitions)
- Enables multiple repositories per context if needed
- Easier to locate data access logic

---

## Method Categories

### Category 1: CRUD Operations
**Priority: CRITICAL** - Basic data access

#### create(data: dict) → EmailNotification
- **Purpose**: Create single notification
- **Input**: Dictionary with keys:
  ```
  {
    "session_id": int,
    "student_profile_id": int,
    "token": str,
    "token_expires_at": datetime,
    "status": str (default "pending")
  }
  ```
- **Validation**: Model-level validation (constraints, field types)
- **Returns**: Saved EmailNotification instance
- **Error Handling**: 
  - Duplicate (session + student) → IntegrityError
  - Invalid FK → ForeignKey.DoesNotExist
- **Why Important**: Ensures consistent creation logic

#### bulk_create(notifications: List[dict]) → List[EmailNotification]
- **Purpose**: Create multiple notifications efficiently
- **Why Critical**: Session with 200 students needs 200 notifications
- **Performance**: Single database transaction vs 200 individual inserts
- **Input**: List of notification dictionaries
- **Returns**: List of created EmailNotification instances
- **Note**: Django `bulk_create` bypasses signals and save() methods
- **Use Case**: Session creation triggers bulk email generation
- **Example**:
  ```
  Session 123 created → Generate 200 notifications in one query
  ```

#### get_by_id(email_id: int) → EmailNotification
- **Purpose**: Retrieve notification by primary key
- **Raises**: EmailNotification.DoesNotExist if not found
- **Use Case**: Admin viewing specific notification details

#### get_by_token(token: str) → EmailNotification | None
- **Purpose**: Find notification by JWT token
- **Why Critical**: Attendance marking uses token to identify student and session
- **Performance**: Indexed on `token` field for fast lookup
- **Returns**: EmailNotification or None if not found
- **Use Case**: Student clicks email link → validate token → extract session/student
- **Security Note**: Token should be long and random (JWT signature)

#### update_status(email_id: int, new_status: str, sent_at: datetime = None) → EmailNotification
- **Purpose**: Change notification status
- **Status Transitions**:
  - `pending` → `sent` (set sent_at)
  - `pending` → `failed` (sent_at remains NULL)
  - `failed` → `pending` (retry, clear sent_at)
- **Validation**: Enforce allowed transitions (sent cannot change)
- **Returns**: Updated EmailNotification
- **Why Method**: Ensures consistent status updates

#### delete(email_id: int) → None
- **Purpose**: Hard delete notification
- **Use Case**: Cleanup expired/test notifications
- **Note**: Rarely used; notifications preserved for audit trail

---

### Category 2: Status-Based Queries
**Priority: HIGH** - Drive background processing and admin workflows

#### get_pending_emails(limit: int = 100) → QuerySet[EmailNotification]
- **Purpose**: Retrieve pending emails for background worker
- **Query**: `status = 'pending'`
- **Ordering**: `created_at ASC` (FIFO - oldest first)
- **Limit**: Batch size for worker (e.g., 100 emails per task)
- **Why Important**: Worker pulls these to send
- **Optimization**: Index on `status` field
- **Use Case**: Celery task queries this every minute

#### get_failed_emails() → QuerySet[EmailNotification]
- **Purpose**: Retrieve all failed notifications
- **Query**: `status = 'failed'`
- **Ordering**: `created_at DESC` (recent failures first)
- **Use Case**: Admin dashboard showing delivery failures
- **Action**: Admin can retry failed emails

#### count_by_status() → dict
- **Purpose**: Get notification counts grouped by status
- **Returns**: 
  ```
  {
    "pending": 45,
    "sent": 1250,
    "failed": 8
  }
  ```
- **Query**: `GROUP BY status`
- **Use Case**: Admin dashboard statistics

---

### Category 3: Session and Student Queries
**Priority: HIGH** - Context-specific filtering

#### get_by_session(session_id: int) → QuerySet[EmailNotification]
- **Purpose**: Get all notifications for a session
- **Query**: `session_id = ?`
- **Ordering**: `created_at ASC`
- **Use Case**: 
  - Lecturer views "who was notified?"
  - Admin troubleshoots session email issues
- **Related Data**: Prefetch `student_profile` and `student_profile__user` for efficiency

#### get_by_student(student_profile_id: int) → QuerySet[EmailNotification]
- **Purpose**: Get student's notification history
- **Query**: `student_profile_id = ?`
- **Ordering**: `created_at DESC` (recent first)
- **Use Case**: Student support ("I didn't receive email for Session X")

#### exists_for_session_and_student(session_id: int, student_profile_id: int) → bool
- **Purpose**: Check if notification already exists
- **Query**: `session_id = ? AND student_profile_id = ?`
- **Why Important**: Prevent duplicate notifications (though unique constraint catches this)
- **Use Case**: Pre-check before bulk_create to skip duplicates

---

### Category 4: Expiry and Cleanup Queries
**Priority: MEDIUM** - Maintenance and optimization

#### get_expired_tokens() → QuerySet[EmailNotification]
- **Purpose**: Find notifications with expired tokens
- **Query**: `token_expires_at < NOW()`
- **Use Case**: Cleanup job to delete old notifications (optional)
- **Note**: Expired tokens automatically rejected during attendance validation

#### delete_expired(older_than_days: int = 30) → int
- **Purpose**: Bulk delete old expired notifications
- **Query**: `token_expires_at < NOW() - ? days`
- **Returns**: Count of deleted records
- **Why**: Reduce database size, maintain performance
- **When**: Run as periodic cleanup job (weekly/monthly)
- **Important**: Only delete if no audit requirement

---

### Category 5: Statistics and Reporting
**Priority: MEDIUM** - Admin insights

#### get_delivery_statistics(session_id: int = None) → dict
- **Purpose**: Calculate delivery metrics
- **Optional Filter**: Specific session or all notifications
- **Returns**:
  ```
  {
    "total": 1303,
    "pending": 45,
    "sent": 1250,
    "failed": 8,
    "success_rate": 0.994  # sent / (sent + failed)
  }
  ```
- **Use Case**: System health monitoring, session success tracking

---

## Query Optimization Strategies

**Priority: HIGH** - Performance considerations

### 1. Select Related / Prefetch Related
**Why**: Avoid N+1 query problem

```
# Bad: 201 queries (1 for notifications + 200 for student profiles)
notifications = EmailNotification.objects.filter(session_id=123)
for notif in notifications:
    print(notif.student_profile.user.email)  # Each iteration hits DB

# Good: 2 queries (1 for notifications + 1 for profiles)
notifications = EmailNotification.objects.filter(session_id=123)\
    .select_related('student_profile__user')
for notif in notifications:
    print(notif.student_profile.user.email)  # No DB hit
```

### 2. Indexes Are Critical
**Ensure these indexes exist**:
- `status` (for pending/failed queries)
- `token` (for attendance validation)
- `session_id` (for session notifications)
- `student_profile_id` (for student history)

### 3. Bulk Operations
**Use bulk_create for multiple records**:
- 200 individual `create()` calls → 200 transactions
- 1 `bulk_create(200 records)` → 1 transaction
- **Performance gain**: 10-50x faster

---

## Error Handling and Mapping

**Priority: HIGH** - Consistent error responses

### Repository-Level Errors
- **DoesNotExist**: Record not found → Map to domain exception in service
- **IntegrityError**: Unique constraint violated → Map to `DuplicateNotificationError`
- **ValidationError**: Field validation failed → Map to `InvalidNotificationDataError`

### Service-Level Mapping Example
```
Repository raises IntegrityError (duplicate)
    ↓
Service catches and raises DuplicateNotificationError
    ↓
API layer returns 409 Conflict
```

**Why Separate**: Services own business logic and error semantics, repositories stay generic

---

## File Organization

**Priority: MEDIUM** - Maintainability

```
email_notifications/
├── models.py                           # EmailNotification model
├── repositories/
│   ├── __init__.py
│   └── email_repository.py             # EmailNotificationRepository class
├── services/
│   ├── __init__.py
│   ├── jwt_service.py
│   ├── email_service.py
│   └── notification_service.py
├── tests/
│   ├── test_models.py
│   ├── test_repositories.py            # Repository tests here
│   ├── test_services.py
│   └── fixtures.py                     # Test data helpers
```

**Why Separate Folder**:
- Clear separation: `repositories/` vs `services/`
- Easy to locate data access logic
- Enables multiple repository classes if context grows

---

## Testing Repositories

**Priority: HIGH** - Ensure data access reliability

### Test Categories
1. **CRUD tests**: Create, get, update, delete work correctly
2. **Query tests**: Status filters, session filters return correct results
3. **Bulk operations**: bulk_create performance and correctness
4. **Constraint tests**: Unique constraint enforced
5. **Ordering tests**: Results ordered as specified

### Example Test Structure
```
tests/test_repositories.py
- test_create_notification_success
- test_create_duplicate_raises_integrity_error
- test_get_by_token_returns_notification
- test_get_by_token_returns_none_if_not_found
- test_get_pending_emails_ordered_by_created_at
- test_bulk_create_200_notifications_efficient
- test_update_status_pending_to_sent
- test_update_status_sent_to_pending_not_allowed
```

---

## Method Summary

**CRUD**:
- `create` - Single notification
- `bulk_create` - Multiple notifications (efficient)
- `get_by_id` - By primary key
- `get_by_token` - By JWT token (attendance validation)
- `update_status` - Change status and sent_at
- `delete` - Remove notification

**Status Queries**:
- `get_pending_emails` - For background worker
- `get_failed_emails` - For admin retry
- `count_by_status` - Statistics

**Context Queries**:
- `get_by_session` - All notifications for a session
- `get_by_student` - Student's notification history
- `exists_for_session_and_student` - Duplicate check

**Maintenance**:
- `get_expired_tokens` - Cleanup query
- `delete_expired` - Bulk delete old records

**Reporting**:
- `get_delivery_statistics` - Metrics and success rates

---

**Status**: 📋 Complete repository specification ready for implementation

**Key Takeaways**:
1. **bulk_create for efficiency** (1 transaction vs 200)
2. **Status-based queries drive workflow** (pending emails)
3. **Token lookup is critical** (attendance validation)
4. **Indexes on status, token, session, student** (performance)
5. **Separate repositories from services** (testability, clarity)