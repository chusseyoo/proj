attenda# testing_guide.md

Brief: Comprehensive testing strategy for Email Notifications context. Covers models, repositories, services (JWT, SMTP, orchestration), API, integration with other contexts, edge cases, and shared fixtures. Focus on Parts 1-6 and 8 (omit performance and infrastructure tests).

---

## Testing Philosophy

**Why Testing Matters in Email Notifications**:
- **Token security is critical**: Invalid tokens = security breach
- **Delivery reliability**: Failed emails = students miss attendance
- **Cross-context integration**: Must work with Session Management, User Management
- **Async complexity**: Background tasks need careful testing

---

## File Organization

**Priority: HIGH** - Maintainable test structure

```
email_notifications/
└── tests/
    ├── __init__.py
    ├── conftest.py                          # Pytest configuration + shared fixtures
    ├── fixtures.py                          # Test data builders
    ├── test_models.py                       # Part 1: Model tests
    ├── test_repositories.py                 # Part 2: Repository tests
    ├── test_jwt_service.py                  # Part 3: JWT service tests
    ├── test_email_sender_service.py         # Part 3: Email service tests
    ├── test_notification_generation_service.py  # Part 3: Orchestration tests
    ├── test_api.py                          # Part 4: API endpoint tests
    ├── test_integration.py                  # Part 5: Cross-context integration
    └── test_edge_cases.py                   # Part 6: Edge cases and boundaries
```

**Why This Structure**:
- Clear separation by layer (models, repos, services, API)
- Easy to locate specific test
- Fixtures isolated in dedicated file

---

# PART 1: MODEL TESTS

**File**: `tests/test_models.py`

**Purpose**: Validate EmailNotification model constraints, relationships, and methods

**Priority: HIGH** - Foundation for all other tests

## Test Cases

### 1.1 Creation and Constraints
- ✅ **test_create_email_notification_success**
  - Create valid notification with all required fields
  - Verify fields saved correctly
  - Check default status is 'pending'

- ✅ **test_unique_constraint_session_student**
  - Create notification for Session A + Student B
  - Attempt duplicate → Expect IntegrityError
  - Why: Prevent duplicate emails to same student

- ✅ **test_token_expiry_must_be_future**
  - Create notification with `token_expires_at` in past
  - Expect ValidationError
  - Why: CHECK constraint enforcement

- ✅ **test_status_choices_enforced**
  - Attempt invalid status (e.g., "invalid")
  - Expect ValidationError
  - Valid statuses: pending, sent, failed

### 1.2 Nullable Fields
- ✅ **test_sent_at_nullable**
  - Create notification without `sent_at`
  - Verify `sent_at` is NULL
  - Why: Only set when status becomes 'sent'

### 1.3 Foreign Key Relationships
- ✅ **test_cascade_delete_session**
  - Create notification for session
  - Delete session
  - Verify notification also deleted (CASCADE)

- ✅ **test_cascade_delete_student**
  - Create notification for student
  - Delete student profile
  - Verify notification deleted (CASCADE)
  - Why: GDPR compliance

### 1.4 Model Methods
- ✅ **test_is_expired_returns_true_when_past**
  - Create notification with `token_expires_at` in past
  - Call `is_expired()` → Expect True

- ✅ **test_is_expired_returns_false_when_future**
  - Create notification with future expiry
  - Call `is_expired()` → Expect False

- ✅ **test_mark_as_sent_updates_status_and_timestamp**
  - Create pending notification
  - Call `mark_as_sent(now)`
  - Verify status='sent' and `sent_at` set

- ✅ **test_mark_as_failed_keeps_sent_at_null**
  - Create pending notification
  - Call `mark_as_failed()`
  - Verify status='failed' and `sent_at` is NULL

---

# PART 2: REPOSITORY TESTS

**File**: `tests/test_repositories.py`

**Purpose**: Validate data access layer without business logic

**Priority: HIGH** - Ensure queries work correctly

## Test Cases

### 2.1 CRUD Operations
- ✅ **test_create_notification**
  - Repository creates and returns notification
  - Verify saved to database

- ✅ **test_bulk_create_200_notifications**
  - Create list of 200 notification dicts
  - Call `bulk_create`
  - Verify all 200 created in database
  - Why: Performance test for session with many students

- ✅ **test_get_by_id_success**
  - Create notification
  - Retrieve by ID
  - Verify fields match

- ✅ **test_get_by_id_not_found**
  - Query non-existent ID
  - Expect DoesNotExist exception

- ✅ **test_get_by_token_success**
  - Create notification with token "ABC123"
  - Query by token
  - Verify found

- ✅ **test_get_by_token_returns_none_if_not_found**
  - Query invalid token
  - Return None (not exception)

### 2.2 Status Queries
- ✅ **test_get_pending_emails_returns_pending_only**
  - Create 5 pending, 3 sent, 2 failed
  - Query `get_pending_emails()`
  - Verify returns exactly 5 pending notifications

- ✅ **test_get_pending_emails_ordered_by_created_at**
  - Create 3 pending with different timestamps
  - Query pending
  - Verify ordered oldest-first (FIFO)

- ✅ **test_get_failed_emails_returns_failed_only**
  - Create mixed statuses
  - Query `get_failed_emails()`
  - Verify only failed returned

- ✅ **test_count_by_status**
  - Create 10 pending, 20 sent, 5 failed
  - Call `count_by_status()`
  - Verify counts correct

### 2.3 Context Queries
- ✅ **test_get_by_session_returns_all_notifications**
  - Create 5 notifications for Session A, 3 for Session B
  - Query by Session A
  - Verify returns 5

- ✅ **test_get_by_student_returns_history**
  - Create 3 notifications for Student X (different sessions)
  - Query by student
  - Verify returns 3, ordered by created_at DESC

### 2.4 Update Operations
- ✅ **test_update_status_pending_to_sent**
  - Create pending notification
  - Update status to 'sent' with timestamp
  - Verify status and sent_at updated

- ✅ **test_update_status_failed_to_pending_for_retry**
  - Create failed notification
  - Update status to 'pending'
  - Verify status changed, sent_at cleared

---

# PART 3: SERVICE TESTS

**Priority: CRITICAL** - Business logic must be correct

## 3.1 JWTTokenService Tests

**File**: `tests/test_jwt_service.py`

### Test Cases
- ✅ **test_generate_token_creates_valid_jwt**
  - Generate token for student 123, session 456
  - Decode and verify payload contains correct IDs
  - Verify signature valid

- ✅ **test_generate_token_includes_expiry**
  - Generate token with expiry in 60 minutes
  - Decode payload
  - Verify `exp` field present and correct

- ✅ **test_validate_token_returns_true_for_valid**
  - Generate valid token
  - Call `validate_token` immediately
  - Expect True

- ✅ **test_validate_token_returns_false_for_expired**
  - Generate token with expiry in past (mock time)
  - Call `validate_token`
  - Expect False

- ✅ **test_validate_token_returns_false_for_tampered**
  - Generate valid token
  - Modify token string (change 1 character)
  - Call `validate_token`
  - Expect False (signature invalid)

- ✅ **test_decode_token_returns_payload**
  - Generate token
  - Decode
  - Verify student_profile_id and session_id correct

- ✅ **test_decode_token_raises_expired_error**
  - Generate expired token
  - Attempt decode
  - Expect ExpiredTokenError

- ✅ **test_decode_token_raises_invalid_error_for_bad_signature**
  - Create malformed token
  - Attempt decode
  - Expect InvalidTokenError

## 3.2 EmailSenderService Tests

**File**: `tests/test_email_sender_service.py`

**Note**: Mock SMTP (don't send real emails in tests)

### Test Cases
- ✅ **test_send_attendance_notification_success**
  - Mock SMTP send_mail
  - Call `send_attendance_notification` with valid context
  - Verify send_mail called with correct params
  - Verify returns True

- ✅ **test_send_attendance_notification_smtp_failure**
  - Mock SMTP to raise exception
  - Call send method
  - Verify returns False (not exception)
  - Why: Service handles SMTP errors gracefully

- ✅ **test_email_template_rendering**
  - Provide context with student name, course info
  - Generate email body
  - Verify student name appears in body
  - Verify attendance link appears

- ✅ **test_send_bulk_emails_success**
  - Mock SMTP
  - Call `send_bulk_emails` with 10 emails
  - Verify returns summary with 10 sent, 0 failed

- ✅ **test_send_bulk_emails_partial_failure**
  - Mock SMTP to fail on 3rd and 7th emails
  - Send 10 emails
  - Verify summary: 8 sent, 2 failed

## 3.3 NotificationGenerationService Tests

**File**: `tests/test_notification_generation_service.py`

**Note**: Mock repositories and cross-context dependencies

### Test Cases
- ✅ **test_generate_notifications_for_session_success**
  - Mock session with 3 eligible students
  - Call `generate_notifications_for_session`
  - Verify 3 notifications created
  - Verify all have unique tokens
  - Verify all status='pending'

- ✅ **test_generate_notifications_calculates_expiry_correctly**
  - Session starts at 08:00
  - Token expiry should be 09:00 (60 mins later)
  - Verify `token_expires_at` correct

- ✅ **test_generate_notifications_respects_stream_targeting**
  - Session targets Stream A (has 5 students)
  - Program has 20 students total
  - Verify only 5 notifications created (Stream A only)

- ✅ **test_generate_notifications_entire_program_when_stream_null**
  - Session has `stream_id=NULL`
  - Program has 20 active students
  - Verify 20 notifications created

- ✅ **test_generate_notifications_excludes_inactive_students**
  - Program has 5 students (3 active, 2 inactive)
  - Verify only 3 notifications created

- ✅ **test_generate_notifications_session_not_found**
  - Call with invalid session_id
  - Expect SessionNotFoundError

- ✅ **test_retry_failed_notifications_resets_status**
  - Create 3 failed notifications
  - Call `retry_failed_notifications` with IDs
  - Verify all reset to 'pending'
  - Verify sent_at cleared

---

# PART 4: API TESTS

**File**: `tests/test_api.py`

**Purpose**: Validate HTTP endpoints, auth, and error responses

**Priority: HIGH** - Contract testing

## Test Cases

### 4.1 Internal Endpoint: Generate Notifications
- ✅ **test_generate_notifications_success_201**
  - POST `/internal/sessions/123/notifications`
  - Valid service token
  - Expect 201, response has `notifications_created`

- ✅ **test_generate_notifications_requires_internal_auth**
  - POST without service token
  - Expect 401 Unauthorized

- ✅ **test_generate_notifications_session_not_found_404**
  - POST with invalid session_id
  - Expect 404

- ✅ **test_generate_notifications_idempotent_409**
  - Generate notifications for session
  - Attempt again
  - Expect 409 Conflict (already exists)

### 4.2 Admin: Retry Failed
- ✅ **test_retry_failed_notifications_admin_success_200**
  - Admin JWT token
  - POST `/admin/notifications/retry` with failed email_ids
  - Expect 200, response has `retried` count

- ✅ **test_retry_failed_notifications_non_admin_403**
  - Lecturer JWT token (not admin)
  - POST retry endpoint
  - Expect 403 Forbidden

- ✅ **test_retry_invalid_email_ids_400**
  - POST with malformed email_ids
  - Expect 400 Bad Request

### 4.3 Monitoring: List Notifications
- ✅ **test_list_session_notifications_lecturer_success_200**
  - Lecturer creates session with 5 students
  - GET `/sessions/123/notifications`
  - Expect 200, 5 notifications in response

- ✅ **test_list_session_notifications_wrong_lecturer_403**
  - Lecturer A creates session
  - Lecturer B tries to view
  - Expect 403 Forbidden

- ✅ **test_list_session_notifications_admin_can_view_any**
  - Admin token
  - GET any session's notifications
  - Expect 200

- ✅ **test_list_notifications_filter_by_status**
  - Session has 3 sent, 2 failed
  - GET with `?status=failed`
  - Expect 2 results

### 4.4 Monitoring: Statistics
- ✅ **test_statistics_admin_only_200**
  - Admin token
  - GET `/admin/notifications/statistics`
  - Expect 200 with counts

- ✅ **test_statistics_non_admin_403**
  - Lecturer token
  - GET statistics
  - Expect 403

---

# PART 5: INTEGRATION TESTS

**File**: `tests/test_integration.py`

**Purpose**: Test cross-context interactions (no mocks)

**Priority: HIGH** - Ensure contexts work together

## Test Cases

### 5.1 Session Management Integration
- ✅ **test_session_creation_triggers_notification_generation**
  - Create session via Session Management API
  - Verify EmailNotification records created
  - Verify tokens generated
  - Why: End-to-end workflow

- ✅ **test_notification_includes_session_details_in_email**
  - Create session with course "CS201"
  - Generate notifications
  - Verify email template includes "CS201"
  - Why: Ensure session data flows correctly

### 5.2 User Management Integration
- ✅ **test_notification_uses_student_email_from_user_table**
  - Student has email "john@example.com" in User table
  - Generate notification
  - Verify email sent to "john@example.com"
  - Why: Email retrieval from User Management

- ✅ **test_inactive_students_excluded**
  - Program has 5 students (1 inactive)
  - Create session
  - Verify only 4 notifications created
  - Why: Only active students get emails

### 5.3 Attendance Recording Integration
- ✅ **test_token_validation_in_attendance_flow**
  - Generate notification with token
  - Pass token to Attendance Recording (mock)
  - Verify token decodes correctly
  - Verify student_id and session_id extracted
  - Why: Token must work downstream

---

# PART 6: EDGE CASE TESTS

**File**: `tests/test_edge_cases.py`

**Purpose**: Boundary conditions and unusual scenarios

**Priority: MEDIUM** - Robustness

## Test Cases

### 6.1 Boundary Conditions
- ✅ **test_token_expiry_at_exact_second**
  - Token expires at 09:00:00
  - Validate at 09:00:00 exactly
  - Expect expired (>= expiry time)

- ✅ **test_session_with_zero_eligible_students**
  - Session targets Stream A (no students)
  - Generate notifications
  - Verify 0 created (no error)
  - Why: Empty result set is valid

- ✅ **test_bulk_create_with_empty_list**
  - Call `bulk_create([])`
  - Verify no error, returns empty list

### 6.2 Data Quality
- ✅ **test_student_with_invalid_email**
  - Student has email "invalid-email"
  - Generate notification
  - Send email (mocked SMTP)
  - Verify status='failed'
  - Why: Handle bad data gracefully

- ✅ **test_very_long_token_stored_correctly**
  - JWT tokens can be 500+ characters
  - Create notification with long token
  - Retrieve and verify full token

### 6.3 Timing and Race Conditions
- ✅ **test_concurrent_notification_generation_for_same_session**
  - Two processes try to generate notifications simultaneously
  - Unique constraint prevents duplicates
  - One succeeds, other fails gracefully

- ✅ **test_notification_created_then_session_deleted**
  - Create notification
  - Delete session (CASCADE)
  - Verify notification also deleted

---

# PART 8: FIXTURES

**File**: `tests/fixtures.py` and `tests/conftest.py`

**Purpose**: Reusable test data builders

**Priority: HIGH** - Reduce test duplication

## Shared Fixtures

### 8.1 Model Fixtures
```python
@pytest.fixture
def session(db):
    """Create test session"""
    return Session.objects.create(
        program_id=1,
        course_id=10,
        lecturer_id=5,
        stream_id=None,
        time_created=now(),
        time_ended=now() + timedelta(hours=2),
        latitude=Decimal('-1.28333'),
        longitude=Decimal('36.81666')
    )

@pytest.fixture
def student_profile(db):
    """Create test student with user"""
    user = User.objects.create(
        email="student@example.com",
        first_name="John",
        is_active=True
    )
    return StudentProfile.objects.create(
        user=user,
        student_id="ST001",
        program_id=1
    )

@pytest.fixture
def email_notification(db, session, student_profile):
    """Create test email notification"""
    return EmailNotification.objects.create(
        session=session,
        student_profile=student_profile,
        token="test_token_abc123",
        token_expires_at=now() + timedelta(hours=1),
        status='pending'
    )
```

### 8.2 Service Fixtures
```python
@pytest.fixture
def jwt_service():
    """JWTTokenService with test secret"""
    return JWTTokenService(secret_key="test_secret")

@pytest.fixture
def email_repository(db):
    """EmailNotificationRepository"""
    return EmailNotificationRepository()

@pytest.fixture
def notification_service(jwt_service, email_repository):
    """NotificationGenerationService with mocked deps"""
    return NotificationGenerationService(
        jwt_service=jwt_service,
        repository=email_repository,
        # Mock cross-context services
    )
```

### 8.3 API Fixtures
```python
@pytest.fixture
def admin_client(client):
    """API client with admin JWT"""
    token = generate_jwt(user_id=1, role='admin')
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client

@pytest.fixture
def lecturer_client(client):
    """API client with lecturer JWT"""
    token = generate_jwt(user_id=2, role='lecturer')
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client
```

### 8.4 Helper Functions
```python
def create_bulk_notifications(session, count=10):
    """Helper to create multiple notifications"""
    students = create_students(count)
    return [
        EmailNotification.objects.create(
            session=session,
            student_profile=student,
            token=f"token_{i}",
            token_expires_at=now() + timedelta(hours=1),
            status='pending'
        )
        for i, student in enumerate(students)
    ]
```

---

## Testing Tools and Libraries

**Priority: MEDIUM** - Tooling setup

### Required Libraries
- **pytest**: Test framework
- **pytest-django**: Django integration
- **factory-boy**: Test data factories (alternative to fixtures)
- **freezegun**: Mock time for expiry tests
- **responses** or **requests-mock**: Mock HTTP requests
- **unittest.mock**: Mock services and SMTP

### Configuration
```python
# pytest.ini or conftest.py
DJANGO_SETTINGS_MODULE = 'project.settings.test'
python_files = tests.py test_*.py *_tests.py
```

---

## Test Coverage Goals

**Priority: HIGH** - Quality metrics

### Minimum Coverage Targets
- **Models**: 100% (simple, easy to cover)
- **Repositories**: 95%+ (data access critical)
- **Services**: 90%+ (core business logic)
- **API**: 85%+ (HTTP layer)
- **Overall**: 90%+

### Critical Paths (Must be 100%)
- Token generation and validation
- Notification creation for eligible students
- Status transitions (pending → sent/failed)
- Unique constraint enforcement

---

**Status**: 📋 Complete testing guide ready for implementation

**Key Takeaways**:
1. **Token security tests are critical** (JWT validation)
2. **Mock SMTP in tests** (no real emails)
3. **Integration tests verify cross-context** (Session, User Management)
4. **Fixtures reduce duplication** (reusable test data)
5. **Focus on Parts 1-6, 8** (models, repos, services, API, integration, edge cases, fixtures)
