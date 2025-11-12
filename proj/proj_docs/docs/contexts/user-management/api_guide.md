# api_guide.md

This file provides a brief overview of the API endpoints for User Management. It lists key routes, request/response formats, authentication, and error handling strategies.

---

## Key Endpoints

### Registration (Separate endpoints by role)
- `POST /api/users/register/lecturer` - Lecturer self-registration (returns tokens for immediate login)
- `POST /api/users/register/student` - Register student (admin only, no password, no tokens)
- `POST /api/users/register/admin` - Register new admin (existing admin only, no tokens)

### Authentication
- `POST /api/users/login` - Authenticate user and receive JWT tokens
- `POST /api/users/refresh` - Refresh access token using refresh token

### User Management
- `GET /api/users/{user_id}` - Retrieve user details by ID
- `PUT /api/users/{user_id}` - Update user information
- `DELETE /api/users/{user_id}` - Deactivate user account

### Profile Management (Nested Resources)
- `GET /api/users/{user_id}/student-profile` - Get student profile
- `PUT /api/users/{user_id}/student-profile` - Update student profile
- `GET /api/users/{user_id}/lecturer-profile` - Get lecturer profile
- `PUT /api/users/{user_id}/lecturer-profile` - Update lecturer profile

---

## Request/Response Examples

### POST /api/users/register/lecturer
**Request:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@university.edu",
  "password": "SecurePass123!",
  "department_name": "Computer Science"
}
```

**Response (201):**
```json
{
  "user_id": 42,
  "email": "john.doe@university.edu",
  "role": "Lecturer",
  "is_active": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo0MiwiZW1haWwiOiJqb2huLmRvZUB1bml2ZXJzaXR5LmVkdSIsInJvbGUiOiJMZWN0dXJlciIsImV4cCI6MTczMTQzOTIwMCwiaWF0IjoxNzMxNDM4MzAwLCJ0eXBlIjoiYWNjZXNzIiwianRpIjoiYWJjZDEyMzQtNTY3OC05MGFiLWNkZWYtMTIzNDU2Nzg5MGFiIn0...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo0MiwiZXhwIjoxNzMyMDQzMTAwLCJpYXQiOjE3MzE0MzgzMDAsInR5cGUiOiJyZWZyZXNoIiwianRpIjoiZGVmZzQ1NjctODkwMS0yM2NkLWVmZ2gtNDU2Nzg5MDEyM2NkIn0..."
}
```

### POST /api/users/register/student (Admin only)
**Request:**
```json
{
  "student_id": "BCS/234344",
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane.smith@university.edu",
  "program_id": 5,
  "stream_id": 2,
  "year_of_study": 2
}
```

**Response (201):**
```json
{
  "user_id": 43,
  "student_profile_id": 123,
  "student_id": "BCS/234344",
  "email": "jane.smith@university.edu",
  "role": "Student",
  "is_active": true
}
```

**Note:** Student registration does NOT return tokens. Students use passwordless authentication via email links. `qr_code_data` is derived from `student_id` and not accepted in the request body (it may appear in profile detail responses as a read-only field).

### POST /api/users/register/admin (Admin only)
**Request:**
```json
{
  "first_name": "Alice",
  "last_name": "Admin",
  "email": "alice.admin@university.edu",
  "password": "AdminPass123!"
}
```

**Response (201):**
```json
{
  "user_id": 44,
  "email": "alice.admin@university.edu",
  "role": "Admin",
  "is_active": true
}
```

**Note:** Admin registration does NOT return tokens. New admins must login separately.

### POST /api/users/login
**Request:**
```json
{
  "email": "john.doe@university.edu",
  "password": "SecurePass123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "user_id": 42,
    "email": "john.doe@university.edu",
    "role": "Lecturer"
  }
}
```

### GET /api/users/{user_id}
**Response (200):**
```json
{
  "user_id": 42,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@university.edu",
  "role": "Lecturer",
  "is_active": true,
  "date_joined": "2025-01-15T10:30:00Z"
}
```

### GET /api/users/{user_id}/student-profile
**Response (200):**
```json
{
  "student_profile_id": 123,
  "student_id": "BCS/234344",
  "user_id": 42,
  "program_id": 5,
  "stream_id": 2,
  "year_of_study": 2,
  "qr_code_data": "BCS/234344"
}
```

### GET /api/users/{user_id}/lecturer-profile
**Response (200):**
```json
{
  "lecturer_id": 15,
  "user_id": 42,
  "department_name": "Computer Science"
}
```

---

## Authentication & JWT Tokens

### Authentication Methods
- **Admin & Lecturer**: Email + Password (traditional login)
- **Student**: Passwordless JWT tokens from email links
- All authenticated endpoints require: `Authorization: Bearer <access_token>`

### JWT Token Specifications

#### Access Token (15-minute expiry)
**Purpose:** Short-lived token for API authentication

**Claims:**
```json
{
  "user_id": 42,              // User's primary key
  "email": "user@example.com", // User's email address
  "role": "Lecturer",          // User role: Admin, Lecturer, or Student
  "exp": 1731439200,           // Expiry timestamp (15 minutes from iat)
  "iat": 1731438300,           // Issued at timestamp
  "type": "access",            // Token type identifier
  "jti": "abcd1234-5678-90ab-cdef-1234567890ab" // Unique token ID (UUID)
}
```

**Usage:**
- Include in `Authorization: Bearer <access_token>` header
- Automatically validated by `JWTAuthentication` backend
- Expired tokens return `401 Unauthorized`
- Invalid tokens return `401 Unauthorized`

#### Refresh Token (7-day expiry)
**Purpose:** Long-lived token to obtain new access tokens

**Claims:**
```json
{
  "user_id": 42,              // User's primary key
  "exp": 1732043100,          // Expiry timestamp (7 days from iat)
  "iat": 1731438300,          // Issued at timestamp
  "type": "refresh",          // Token type identifier
  "jti": "defg4567-8901-23cd-efgh-4567890123cd" // Unique token ID (UUID)
}
```

**Usage:**
- Send to `POST /api/users/refresh` endpoint
- Returns new access token
- Minimal claims (only user_id) for security
- Cannot be used for API authentication (must use access token)

#### Student Attendance Token (2-hour expiry)
**Purpose:** Time-limited token for marking attendance via email link

**Claims:**
```json
{
  "student_profile_id": 123,  // Student profile ID
  "session_id": 456,          // Session ID for attendance
  "exp": 1731445500,          // Expiry timestamp (2 hours from iat)
  "type": "attendance"        // Token type identifier
}
```

**Usage:**
- Embedded in email links sent to students
- Valid only for specific student and session
- Cannot be reused for different sessions

### Token Security
- **Algorithm:** HS256 (HMAC with SHA-256)
- **Secret Key:** Stored in environment variable (never hardcoded)
- **Signature Verification:** All tokens verified on each request
- **Expiry Enforcement:** Expired tokens automatically rejected
- **Type Validation:** Token type must match expected type

### Token Refresh Flow
1. Client detects access token is expired (401 response)
2. Client sends refresh token to `POST /api/users/refresh`
3. Server validates refresh token
4. Server checks user is still active
5. Server generates new access token with new `exp` and `jti`
6. Client receives new access token
7. Client uses new access token for subsequent requests

**Note:** Refresh tokens cannot be refreshed. User must login again after 7 days.

---

## Error Handling

### HTTP Status Codes
- `200` - OK (successful GET, PUT, DELETE)
- `201` - Created (successful POST)
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource doesn't exist)
- `409` - Conflict (duplicate email/student_id)
- `500` - Internal Server Error

### Error Response Format
```json
{
  "error": "Error message",
  "details": {
    "field_name": ["error description"]
  }
}
```

### Common Errors
**400 - Validation Error:**
```json
{
  "error": "Validation failed",
  "details": {
    "email": ["Email already exists"],
    "student_id": ["Invalid format. Expected: ABC/123456"]
  }
}
```

**401 - Unauthorized:**
```json
{
  "error": "Authentication credentials were not provided"
}
```

**403 - Forbidden:**
```json
{
  "error": "You do not have permission to perform this action"
}
```

**404 - Not Found:**
```json
{
  "error": "User with id 999 not found"
}
```

**409 - Conflict:**
```json
{
  "error": "A user with this email already exists"
}
```

---

## Custom Exception Handler

**File:** `interfaces/api/exceptions/exception_handler.py`

**Purpose:** Maps domain exceptions to appropriate HTTP status codes and response formats. Registered in DRF settings as the custom exception handler.

### Exception Mapping Table

| Domain Exception | HTTP Status | When Raised |
|-----------------|-------------|-------------|
| **404 - Not Found** | | |
| `UserNotFoundError` | 404 | User lookup by ID or email fails |
| `StudentNotFoundError` | 404 | Student profile not found |
| `LecturerNotFoundError` | 404 | Lecturer profile not found |
| `ProgramNotFoundError` | 404 | Referenced program doesn't exist |
| **409 - Conflict** | | |
| `EmailAlreadyExistsError` | 409 | Duplicate email during registration |
| `StudentIdAlreadyExistsError` | 409 | Duplicate student ID during registration |
| **401 - Unauthorized** | | |
| `InvalidCredentialsError` | 401 | Wrong email/password during login |
| `InvalidPasswordError` | 401 | Wrong old password during change |
| `ExpiredTokenError` | 401 | JWT token has expired |
| `InvalidTokenError` | 401 | JWT token is malformed |
| `InvalidTokenTypeError` | 401 | Using wrong token type (access vs refresh) |
| **403 - Forbidden** | | |
| `UnauthorizedError` | 403 | User lacks permission for operation |
| `UserInactiveError` | 403 | Account is deactivated |
| `StudentCannotLoginError` | 403 | Student trying to use password login |
| `StudentCannotHavePasswordError` | 403 | Attempting to set password for student |
| **400 - Bad Request** | | |
| `WeakPasswordError` | 400 | Password doesn't meet strength requirements |
| `InvalidStudentIdFormatError` | 400 | Student ID doesn't match pattern |
| `StreamRequiredError` | 400 | Program has streams but stream_id not provided |
| `StreamNotAllowedError` | 400 | Program has no streams but stream_id provided |
| `StreamNotInProgramError` | 400 | Stream doesn't belong to program |
| `InvalidYearError` | 400 | Year of study not in range 1-4 |
| `InvalidDepartmentNameError` | 400 | Department name validation failed |
| `TokenAlreadyUsedError` | 400 | Reset token already used |

### 401 vs 403 Distinction

**401 Unauthorized:**
- User is NOT authenticated (no credentials or invalid credentials)
- Missing JWT token
- Invalid JWT token
- Expired JWT token
- Wrong email/password
- Response includes `WWW-Authenticate: Bearer realm="api"` header

**403 Forbidden:**
- User IS authenticated but lacks permission
- Wrong role for operation (e.g., non-admin trying to register student)
- Account is deactivated
- Business rule prevents action (e.g., students can't login with password)

**Example:**
```python
# 401 - No token provided
GET /api/users/1
Headers: (no Authorization header)
Response: 401 Unauthorized

# 403 - Valid token but insufficient permissions
GET /api/users/1
Headers: Authorization: Bearer <valid-lecturer-token>
Response: 403 Forbidden (only admin/owner can view)
```

### Custom Handler Configuration

**In `settings.py`:**
```python
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'user_management.interfaces.api.exceptions.exception_handler.custom_exception_handler',
    # ...
}
```

### Adding New Exception Mappings

When adding new domain exceptions:

1. **Define exception in domain layer:**
   ```python
   # domain/exceptions/new_exceptions.py
   class NewBusinessRuleError(Exception):
       """Raised when new business rule violated."""
       pass
   ```

2. **Export from domain/exceptions.py:**
   ```python
   from .new_exceptions import NewBusinessRuleError
   __all__ = [..., 'NewBusinessRuleError']
   ```

3. **Import in exception handler:**
   ```python
   from ....domain.exceptions import NewBusinessRuleError
   ```

4. **Add mapping in `handle_domain_exception()`:**
   ```python
   if isinstance(exc, NewBusinessRuleError):
       return Response(
           {'error': str(exc)},
           status=status.HTTP_400_BAD_REQUEST
       )
   ```

5. **Update this documentation table** with new mapping

---

## Notes
- All endpoints follow RESTful conventions
- Profile endpoints use nested resource pattern: `/api/users/{user_id}/profile-type`
- All requests/responses use JSON format
- Timestamps in ISO 8601 format (UTC)