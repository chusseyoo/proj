# api_guide.md

This file provides a brief overview of the API endpoints for User Management. It lists key routes, request/response formats, authentication, and error handling strategies.

---

## Key Endpoints

### User Management
- `POST /api/users/register` - Register a new user (student, lecturer, admin)
- `POST /api/users/login` - Authenticate user and receive JWT token
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

### POST /api/users/register (Lecturer)
**Request:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@university.edu",
  "password": "SecurePass123!",
  "role": "Lecturer",
  "department_name": "Computer Science"
}
```

**Response (201):**
```json
{
  "user_id": 42,
  "email": "john.doe@university.edu",
  "role": "Lecturer",
  "is_active": true
}
```

### POST /api/users/register (Student - Admin only)
**Request:**
```json
{
  "student_id": "BCS/234344",
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane.smith@university.edu",
  "role": "Student",
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

## Authentication
- JWT-based authentication for all endpoints except `/register` and `/login`
- Include token in header: `Authorization: Bearer <token>`
- Students use passwordless JWT tokens from email links

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

## Notes
- All endpoints follow RESTful conventions
- Profile endpoints use nested resource pattern: `/api/users/{user_id}/profile-type`
- All requests/responses use JSON format
- Timestamps in ISO 8601 format (UTC)