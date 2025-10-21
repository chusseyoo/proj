# User Management Bounded Context

## Purpose

This bounded context handles all user-related functionality including registration, authentication, authorization, and account management for three user roles: Admin, Lecturer, and Student.

## Scope

### What This Context Handles
- User account creation and registration
- Authentication (login/logout)
- Authorization (role-based access control)
- Account lifecycle management (activation, deactivation)
- Password management (hashing, reset)
- User profile management

### What This Context Does NOT Handle
- Academic structures (programs, streams, courses) → handled by Academic Structure Context
- Session creation → handled by Session Management Context
- Attendance recording → handled by Attendance Recording Context
- Email notifications → handled by Email Notification Context

## Core Entities

### User
- **Primary entity** representing all system users
- Attributes:
  - `user_id` (Primary Key, Integer, Auto-increment) - Unique identifier
  - `first_name` (String, NOT NULL) - User's first name
  - `last_name` (String, NOT NULL) - User's last name
  - `email` (String, NOT NULL, UNIQUE) - User's email address
  - `password` (String, **NULLABLE**) - Hashed password
    - **NULL for Students** (they use passwordless JWT authentication)
    - **REQUIRED for Admin and Lecturer** (they use email + password login)
  - `role` (Enum, NOT NULL) - User role: `Admin`, `Lecturer`, or `Student`
  - `is_active` (Boolean, NOT NULL, Default: True) - Account activation status
  - `date_joined` (DateTime, NOT NULL, Auto-set) - Account creation timestamp

**Important Notes:**
- Email must be unique across all users
- Password is nullable because Students don't have passwords
- Role determines which profile table is used (LecturerProfile or StudentProfile)
- Admin users don't have profile extensions

### LecturerProfile
- **Profile extension** for Lecturer users
- Attributes:
  - `lecturer_id` (Primary Key, Integer, Auto-increment) - Unique identifier
  - `user_id` (Foreign Key → User.user_id, NOT NULL, UNIQUE) - One-to-one relationship
  - `department_name` (String, NOT NULL) - Department/Faculty name

**Important Notes:**
- One-to-one relationship with User (where role = Lecturer)
- Created automatically when a lecturer registers
- CASCADE DELETE: Deleting User deletes LecturerProfile
- `user_id` must be unique (one lecturer profile per user)

### StudentProfile
- **Profile extension** for Student users
- Attributes:
  - `student_profile_id` (Primary Key, Integer, Auto-increment) - Internal database identifier
  - `student_id` (String, NOT NULL, UNIQUE) - Institutional student ID (format: `ABC/123456`)
    - Pattern: 3 uppercase letters + `/` + 6 digits
    - Example: `BCS/234344`, `ENG/123456`
    - Regex: `^[A-Z]{3}/[0-9]{6}$`
  - `user_id` (Foreign Key → User.user_id, NOT NULL, UNIQUE) - One-to-one relationship
  - `program_id` (Foreign Key → Program.program_id, NOT NULL) - Student's enrolled program
  - `stream_id` (Foreign Key → Stream.stream_id, **NULLABLE**) - Optional stream within program
    - **NULL if program has no streams** (`Program.has_streams = False`)
    - **REQUIRED if program has streams** (`Program.has_streams = True`)
  - `year_of_study` (Integer, NOT NULL) - Current academic year (1-4)
  - `qr_code_data` (String, NOT NULL) - QR code content matching `student_id`
    - **Must equal `student_id`** (enforced by CHECK constraint)
    - Example: If `student_id = "BCS/234344"`, then `qr_code_data = "BCS/234344"`

**Important Notes:**
- One-to-one relationship with User (where role = Student)
- References Academic Structure Context via `program_id` and `stream_id`
- CASCADE DELETE: Deleting User deletes StudentProfile
- `student_id` is the business identifier (what's printed on ID cards)
- `student_profile_id` is the internal database identifier (used for foreign keys)
- QR codes are printed externally; system only validates the data
- `stream_id` nullability depends on whether the program has streams

## Business Rules

### User Registration

1. **Admin**: 
   - Created by system initialization or other admins
   - Requires email and password
   - No profile extension
   - Automatically activated (`is_active = True`)

2. **Lecturer**: 
   - Self-registration via web interface
   - Requires: first_name, last_name, email, password, department_name
   - Automatically activated (`is_active = True`) - **no admin approval needed**
   - LecturerProfile created automatically
   - Can immediately create courses and sessions

3. **Student**: 
   - Registered by admin only
   - Requires: student_id (ABC/123456 format), first_name, last_name, email, program_id, year_of_study
   - Optional: stream_id (only if program has streams)
   - **No password** (`password = NULL`) - uses passwordless authentication via email links
   - StudentProfile created automatically
   - `qr_code_data` automatically set to match `student_id`

### Authentication

- **Admin & Lecturer**: Email + Password (traditional login)
  - Password must be hashed using bcrypt or Argon2
  - Returns JWT access token + refresh token
  
- **Student**: JWT token from email links (passwordless)
  - No login page for students
  - Access granted via time-limited JWT tokens sent in emails
  - Token contains: `student_profile_id`, `session_id`, `exp` (expiry)

### Authorization

- **Admin**: Full system access
  - Manage all users (create, deactivate, reactivate, update)
  - Manage academic structures (programs, streams, courses)
  - View all reports across all sessions
  - Cannot create sessions (only lecturers can)

- **Lecturer**: Limited to own resources
  - Manage own courses only
  - Create sessions for own courses only
  - View attendance for own sessions only
  - Generate reports for own sessions only
  - Cannot access other lecturers' data
  - Cannot manage users or academic structures

- **Student**: Minimal access
  - Mark attendance via email links only
  - No direct login or dashboard access
  - Cannot view other students' attendance
  - No administrative capabilities

### Account States

- `is_active = True`: Account can be used
  - User can login (Admin/Lecturer)
  - User can receive emails and mark attendance (Student)
  
- `is_active = False`: Account is deactivated
  - Cannot login
  - Cannot perform any actions
  - Email links will not work (Students)
  - Admin can reactivate later

**Important Notes:**
- Deactivating a User does NOT delete data (soft delete)
- Deactivating a Lecturer deactivates all their sessions
- Deactivating a Student prevents them from marking attendance
- Only Admin can deactivate/reactivate accounts

## Validation Rules

### Email Validation
- Must be valid email format
- Must be unique across all users
- Cannot be changed after registration (for simplicity)

### Password Validation (Admin & Lecturer only)
- Minimum 8 characters
- Must contain: uppercase, lowercase, digit, special character
- Hashed using bcrypt (cost factor: 12) or Argon2

### Student ID Validation
- Must match pattern: `^[A-Z]{3}/[0-9]{6}$`
- Must be unique across all students
- Program code (first 3 letters) should match the student's enrolled program code
- Cannot be changed after registration

### Department Name Validation (Lecturer)
- Minimum 3 characters
- Maximum 100 characters
- No special validation (free text)

### Year of Study Validation (Student)
- Must be integer between 1 and 4
- Represents current academic year

## Database Constraints

### User Table
```sql
CREATE TABLE users (
  user_id SERIAL PRIMARY KEY,
  first_name VARCHAR(50) NOT NULL,
  last_name VARCHAR(50) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  password VARCHAR(255),  -- NULLABLE for students
  role VARCHAR(20) NOT NULL CHECK (role IN ('Admin', 'Lecturer', 'Student')),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  date_joined TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

### LecturerProfile Table
```sql
CREATE TABLE lecturer_profiles (
  lecturer_id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
  department_name VARCHAR(100) NOT NULL
);

CREATE INDEX idx_lecturer_profiles_user_id ON lecturer_profiles(user_id);
```

### StudentProfile Table
```sql
CREATE TABLE student_profiles (
  student_profile_id SERIAL PRIMARY KEY,
  student_id VARCHAR(20) NOT NULL UNIQUE,
  user_id INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
  program_id INTEGER NOT NULL REFERENCES programs(program_id),
  stream_id INTEGER REFERENCES streams(stream_id),  -- NULLABLE
  year_of_study INTEGER NOT NULL CHECK (year_of_study BETWEEN 1 AND 4),
  qr_code_data VARCHAR(20) NOT NULL,
  
  CONSTRAINT valid_student_id_format CHECK (student_id ~ '^[A-Z]{3}/[0-9]{6}$'),
  CONSTRAINT qr_matches_student_id CHECK (qr_code_data = student_id)
);

CREATE UNIQUE INDEX idx_student_profiles_student_id ON student_profiles(student_id);
CREATE INDEX idx_student_profiles_user_id ON student_profiles(user_id);
CREATE INDEX idx_student_profiles_program_stream ON student_profiles(program_id, stream_id);
```

**Important Constraint Notes:**
- `ON DELETE CASCADE`: Deleting a User automatically deletes their profile
- `UNIQUE` on `user_id`: One profile per user
- `CHECK` constraint on `student_id`: Enforces format pattern
- `CHECK` constraint on `qr_code_data`: Must match `student_id`
- `stream_id` nullable but required if program has streams (enforced in application layer)

## Django Implementation Structure

This context will be implemented as a Django app with the following structure:

```
user_management/
├── models.py           # User, LecturerProfile, StudentProfile models
├── repositories.py     # UserRepository, LecturerRepository, StudentRepository
├── services.py         # UserService, AuthenticationService, PasswordService
├── handlers.py         # Application layer command/query handlers
├── views.py           # API endpoints (presentation layer)
├── serializers.py     # Request/response serialization
├── validators.py      # Input validation logic
├── permissions.py     # Role-based permission classes
├── urls.py            # URL routing
├── tests/             # Unit and integration tests
└── migrations/        # Database migrations
```

## Integration Points

### Outbound Dependencies (What We Call)
- **Infrastructure**: 
  - Database (PostgreSQL)
  - Password hashing (bcrypt/Argon2)
  - JWT generation (PyJWT)
  
- **Academic Structure Context**: 
  - Validate `program_id` exists when creating StudentProfile
  - Validate `stream_id` exists and belongs to program when creating StudentProfile
  - Check if program `has_streams` to determine if `stream_id` is required

### Inbound Dependencies (Who Calls Us)
- **Session Management Context**: 
  - Get lecturer info (`lecturer_id`, `user_id`) when creating sessions
  - Validate lecturer exists and is active
  
- **Attendance Recording Context**: 
  - Get student info (`student_profile_id`, `student_id`, `program_id`, `stream_id`) when marking attendance
  - Validate student exists and is active
  
- **Email Notification Context**: 
  - Get student email addresses (`User.email` via `StudentProfile.user_id`)
  - Get student names for email personalization
  
- **Reporting Context**: 
  - Get user info for report generation
  - Get lecturer name for report headers
  - Get student names for attendance lists

## Files in This Context

### 1. `README.md` (this file)
Overview of the bounded context

### 2. `models_guide.md`
Step-by-step guide for creating Django models:
- User model (with nullable password)
- LecturerProfile model
- StudentProfile model (with student_id format validation)
- Model relationships and constraints
- Model methods and properties

### 3. `repositories_guide.md`
Guide for creating repository layer:
- UserRepository (CRUD operations)
- LecturerRepository
- StudentRepository
- Query patterns
- Handling nullable fields

### 4. `services_guide.md`
Guide for creating domain services:
- UserService (business logic)
- AuthenticationService (login/logout, handle null passwords)
- PasswordService (hashing, validation)
- RegistrationService (handle different registration flows)

### 5. `handlers_guide.md`
Guide for creating application layer handlers:
- RegisterLecturerHandler (auto-activate)
- RegisterStudentHandler (by admin, no password, set qr_code_data)
- LoginHandler (email + password, reject if password is null)
- DeactivateUserHandler
- UpdateUserHandler

### 6. `views_guide.md`
Guide for creating API endpoints:
- POST /api/v1/auth/register/lecturer/
- POST /api/v1/auth/login/
- POST /api/v1/admin/students/register/
- PATCH /api/v1/admin/users/{id}/deactivate/
- GET /api/v1/users/me/
- Request/response examples with nullable fields

### 7. `permissions_guide.md`
Guide for implementing role-based access control:
- IsAdmin permission
- IsLecturer permission
- IsStudent permission
- Custom permission classes

### 8. `testing_guide.md`
Guide for writing tests:
- Unit tests for models (test nullable fields)
- Unit tests for services (test student vs lecturer registration)
- Integration tests for handlers
- API endpoint tests (test validation rules)

## Implementation Order

1. **Models** (`models_guide.md`) - Define data structure first
2. **Repositories** (`repositories_guide.md`) - Data access layer
3. **Services** (`services_guide.md`) - Business logic
4. **Handlers** (`handlers_guide.md`) - Application layer orchestration
5. **Serializers & Validators** (part of `views_guide.md`) - Input/output handling
6. **Views** (`views_guide.md`) - HTTP endpoints
7. **Permissions** (`permissions_guide.md`) - Access control
8. **Tests** (`testing_guide.md`) - Verification

## Next Steps

After reading this overview:
1. Review the scope and business rules
2. **Verify nullable attributes** (password, stream_id)
3. **Confirm validation rules** (student_id format, qr_code_data constraint)
4. **Check integration points** with other contexts
5. Proceed to read individual guide files in the implementation order above

---

**Status**: 📝 Overview Complete - Ready for detailed guide creation