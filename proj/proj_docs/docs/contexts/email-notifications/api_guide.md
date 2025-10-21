# api_guide.md

Brief: REST API specification for Email Notifications. Minimal public API (mostly internal) with admin retry endpoint and monitoring views. Focuses on operational support rather than direct user interaction.

---

## API Overview

**Scope**: Email Notifications API is primarily **internal** (called by other contexts)

**Why Limited Public API**:
- Email generation triggered automatically by session creation (no manual creation)
- Students don't manage notifications (they just click links in emails)
- Lecturers don't interact with notifications directly
- Only admins need operational endpoints (retry, monitoring)

**Key Endpoints**:
1. **Internal**: Generate notifications (called by Session Management)
2. **Admin**: Retry failed emails
3. **Monitoring**: View notification status for sessions

---

## Conventions

- **Base path**: `/api/email-notifications/v1`
- **Auth**: JWT Bearer tokens
- **Content-Type**: `application/json`
- **Pagination**: page (1-based), page_size (default 20, max 100) where applicable
- **Error envelope**: Consistent format across all endpoints

### Standard Error Response
```json
{
  "error": {
    "code": "SessionNotFoundError",
    "message": "Session with id 999 does not exist",
    "details": {
      "session_id": 999
    }
  }
}
```

### Standard Success Response (Operations)
```json
{
  "status": "success",
  "message": "Operation completed",
  "data": { ... }
}
```

---

## DTOs (Data Transfer Objects)

### EmailNotificationDTO
```json
{
  "email_id": 501,
  "session_id": 123,
  "student_profile_id": 789,
  "student_name": "John Doe",
  "student_email": "john.doe@example.com",
  "token_expires_at": "2025-10-25T09:00:00Z",
  "status": "sent",
  "created_at": "2025-10-25T07:00:00Z",
  "sent_at": "2025-10-25T07:02:15Z"
}
```

**Why These Fields**:
- `email_id`: Unique identifier
- `session_id`, `student_profile_id`: Context references
- `student_name`, `student_email`: Enriched from User Management (not stored)
- `token_expires_at`: When token becomes invalid
- `status`: Delivery state (pending/sent/failed)
- `created_at`: When notification was queued
- `sent_at`: When delivery succeeded (NULL if not sent)

**Security Note**: Token itself is NOT included in DTO (sensitive, no need to expose)

---

## Endpoints

### 1. Internal: Generate Notifications (Session Management Calls This)

**Priority: CRITICAL** - Core workflow

```
POST /internal/sessions/{session_id}/notifications
```

**Purpose**: Create email notifications for all eligible students when session is created

**Authentication**: Internal service token (not public JWT)

**Why Internal**: 
- Only Session Management context should call this
- Triggered automatically, not by user action
- Different auth mechanism (service-to-service)

**Request Body**: None (session_id in URL is sufficient)

**Response (201 Created)**:
```json
{
  "status": "success",
  "data": {
    "session_id": 123,
    "notifications_created": 45,
    "eligible_students": 45
  }
}
```

**Error Responses**:
- **404**: Session not found
- **409**: Notifications already exist for this session (idempotency)
- **500**: Token generation or database error

**Why Separate Endpoint**:
- Clear contract between contexts
- Easy to monitor (log internal API calls)
- Can implement rate limiting if needed

---

### 2. Admin: Retry Failed Notifications

**Priority: HIGH** - Operational support

```
POST /admin/notifications/retry
```

**Purpose**: Admin can retry failed email deliveries (SMTP errors, invalid emails)

**Authentication**: Admin role required (JWT)

**Request Body**:
```json
{
  "email_ids": [502, 505, 508]
}
```

**Response (200 OK)**:
```json
{
  "status": "success",
  "data": {
    "retried": 3,
    "skipped": 0,
    "errors": []
  }
}
```

**Workflow**:
1. Validate all `email_ids` exist
2. Check each notification:
   - If `status = 'failed'` → Reset to `pending`
   - If `status = 'sent'` → Skip (cannot retry sent emails)
3. Background worker picks up pending notifications

**Error Responses**:
- **400**: Invalid email_ids format
- **403**: Not an admin
- **404**: Some email_ids not found

**Why Admin-Only**:
- Prevents abuse (students can't spam system)
- Operational tool for recovering from outages
- Requires understanding of system state

---

### 3. Monitoring: List Notifications for Session

**Priority: MEDIUM** - Support and debugging

```
GET /sessions/{session_id}/notifications
```

**Purpose**: View all notifications for a session (who was notified, delivery status)

**Authentication**: 
- Lecturer (session owner) can view their sessions
- Admin can view any session

**Query Parameters**:
- `status`: Filter by status (pending/sent/failed)
- `page`, `page_size`: Pagination

**Response (200 OK)**:
```json
{
  "results": [
    {
      "email_id": 501,
      "student_name": "John Doe",
      "student_email": "john.doe@example.com",
      "status": "sent",
      "sent_at": "2025-10-25T07:02:15Z"
    },
    {
      "email_id": 502,
      "student_name": "Alice Brown",
      "student_email": "alice.brown@example.com",
      "status": "failed",
      "sent_at": null
    }
  ],
  "total_count": 45,
  "page": 1,
  "page_size": 20,
  "total_pages": 3,
  "has_next": true,
  "has_previous": false
}
```

**Authorization**:
- Lecturer: Only their own sessions
- Admin: Any session

**Use Cases**:
- Lecturer: "Did all my students get notified?"
- Admin: Troubleshoot delivery failures
- Support: "Why didn't Student X receive email?"

**Error Responses**:
- **403**: Not authorized to view this session
- **404**: Session not found

---

### 4. Monitoring: Notification Statistics

**Priority: LOW** - Admin dashboard

```
GET /admin/notifications/statistics
```

**Purpose**: System-wide email delivery statistics

**Authentication**: Admin only

**Query Parameters**:
- `session_id`: Filter by session (optional)
- `from_date`, `to_date`: Date range (optional)

**Response (200 OK)**:
```json
{
  "total": 1303,
  "pending": 45,
  "sent": 1250,
  "failed": 8,
  "success_rate": 0.994,
  "average_delivery_time_seconds": 125
}
```

**Why Useful**:
- Monitor system health
- Identify email delivery issues
- Capacity planning

---

## Validation Rules

**Priority: HIGH** - Enforce at API layer

### For POST /internal/sessions/{session_id}/notifications
- `session_id` must be valid integer
- Session must exist
- Session must have eligible students (warn if 0, don't fail)

### For POST /admin/notifications/retry
- `email_ids` must be non-empty array of integers
- All IDs must exist in database
- Only retry `failed` status notifications

### For GET /sessions/{session_id}/notifications
- `session_id` must be valid integer
- `status` query param (if provided) must be one of: pending, sent, failed
- `page` and `page_size` must be positive integers

---

## Security Considerations

**Priority: CRITICAL**

### 1. Authentication Layers
- **Internal endpoints**: Service token (not user JWT)
  - Why: Prevent users from triggering notification generation
  - Implementation: Shared secret or API key
- **Admin endpoints**: Admin role in JWT
  - Why: Operational tools need protection
- **Monitoring endpoints**: Lecturer or Admin
  - Why: Privacy (lecturers see only their data)

### 2. Authorization Checks
- Lecturers can only view their own session notifications
- Admins bypass ownership checks (full access)
- Students have NO access to this API (they use Attendance Recording)

### 3. Rate Limiting
**Why Important**: Prevent abuse of internal endpoint

- Internal notification generation: 10 requests/minute per session
- Admin retry: 20 requests/minute per admin
- Monitoring queries: 100 requests/minute per user

### 4. Data Exposure
**What NOT to return**:
- JWT tokens (sensitive, can be used for attendance)
- SMTP credentials (environment variables only)
- Full student profile data (only name and email)

---

## Error Handling

**Priority: HIGH** - Consistent error experience

### HTTP Status Codes

| Status | Use Case | Example |
|--------|----------|---------|
| 200 | Success (query) | GET notifications |
| 201 | Success (creation) | POST generate notifications |
| 400 | Invalid input | Malformed email_ids array |
| 401 | Not authenticated | Missing JWT token |
| 403 | Not authorized | Lecturer viewing other's session |
| 404 | Resource not found | Session 999 doesn't exist |
| 409 | Conflict | Notifications already generated |
| 500 | Server error | Database connection failed |
| 502 | Bad gateway | SMTP server unreachable |

### Error Response Format
```json
{
  "error": {
    "code": "SessionNotFoundError",
    "message": "Human-readable message",
    "details": {
      "session_id": 999,
      "timestamp": "2025-10-25T10:00:00Z"
    }
  }
}
```

**Why Structured Errors**:
- Clients can handle errors programmatically
- Consistent format across all contexts
- Details help with debugging

---

## Integration Notes

**Priority: HIGH** - Cross-context coordination

### Session Management Context → Email Notifications
**Flow**: Session created → Call `/internal/sessions/{id}/notifications`

**Contract**:
- Session Management provides: `session_id`
- Email Notifications returns: Count of notifications created
- Async: Notifications queued (status=pending), sent later by background worker

**Error Handling**:
- Session Management should NOT fail if notification generation fails
- Log error and continue (session creation succeeds)
- Admin can retry notifications manually

### Email Notifications → User Management
**Flow**: Fetch student emails for notification list

**Contract**:
- Email Notifications queries: `StudentProfile` and `User.email`
- User Management provides: Active students with valid emails
- No direct API call (database access via repositories)

### Email Notifications → Attendance Recording
**Flow**: Attendance Recording validates tokens

**Contract**:
- Attendance provides: JWT token from student click
- Email Notifications (JWT service) validates token
- Token marked as "used" in Attendance Recording context

---

## File Organization

**Priority: MEDIUM** - Maintainability

```
email_notifications/
├── views.py                        # API views (all endpoints)
│   ├── InternalNotificationView    # POST /internal/sessions/{id}/notifications
│   ├── AdminRetryView              # POST /admin/notifications/retry
│   ├── SessionNotificationsView    # GET /sessions/{id}/notifications
│   └── StatisticsView              # GET /admin/notifications/statistics
├── serializers.py                  # Request/response serialization
│   ├── EmailNotificationSerializer
│   └── RetryRequestSerializer
├── permissions.py                  # Authorization
│   ├── IsAdminUser
│   ├── IsSessionOwnerOrAdmin
│   └── IsInternalService
├── urls.py                         # URL routing
└── tests/
    └── test_api.py                 # API endpoint tests
```

---

## Testing API Endpoints

**Priority: HIGH** - Ensure contract reliability

### Test Categories
1. **Authentication tests**: 401 for missing token, 403 for wrong role
2. **Authorization tests**: Lecturers can't view others' sessions
3. **Validation tests**: 400 for invalid inputs
4. **Happy path tests**: 200/201 for valid requests
5. **Error handling tests**: 404 for missing resources

### Example Test Cases
```
test_generate_notifications_success_201
test_generate_notifications_session_not_found_404
test_generate_notifications_duplicate_409
test_retry_failed_notifications_admin_success_200
test_retry_notifications_non_admin_403
test_list_session_notifications_lecturer_success_200
test_list_session_notifications_wrong_lecturer_403
test_statistics_admin_only_200
```

---

**Status**: 📋 Complete API specification ready for implementation

**Key Takeaways**:
1. **Mostly internal API** (Session Management triggers generation)
2. **Admin retry endpoint** (recover from failures)
3. **Monitoring for lecturers** (view notification status)
4. **Security layers** (internal service token vs user JWT)
5. **Async workflow** (create pending, send later)