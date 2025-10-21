# services_guide.md

Brief: Comprehensive guide for implementing the service layer in User Management. Each service is grouped with its methods, validations, business logic, and error handling. Services should be implemented in separate files within a `services/` folder.

---

## File Organization

**Service Layer Structure:**
```
user_management/
├── services/
│   ├── __init__.py
│   ├── user_service.py           # UserService
│   ├── authentication_service.py  # AuthenticationService
│   ├── password_service.py        # PasswordService
│   ├── registration_service.py    # RegistrationService
│   └── profile_service.py         # ProfileService
├── repositories.py
├── models.py
└── ...
```

**Why Separate Files:**
- Each service has focused responsibility
- Easier to test in isolation
- Clearer dependencies between services
- Simpler code navigation

---

# PART 1: USER SERVICE

## 1.1 UserService Overview

**Purpose:** Handles core user operations (retrieve, update, activate, deactivate).

**File:** `services/user_service.py`

**Dependencies:**
- UserRepository (data access)
- StudentProfileRepository (for student users)
- LecturerProfileRepository (for lecturer users)

**Responsibilities:**
- Get user details
- Update user information
- Activate/deactivate user accounts
- Validate user role
- Check user permissions

---

## 1.2 UserService Methods

### Method: get_user_by_id(user_id)

**Purpose:** Retrieve user details by ID with profile information.

**Parameters:**
- `user_id` (int, required) - User's primary key

**Returns:**
- User object with profile (if exists)

**Business Logic:**
1. Call `user_repository.get_by_id(user_id)`
2. If user is Student, fetch `student_profile` (select_related)
3. If user is Lecturer, fetch `lecturer_profile` (select_related)
4. Return user with profile

**Exceptions:**
- `UserNotFoundError` if user doesn't exist

**Example Flow:**
```
Input: user_id = 42
↓
Repository: user_repository.get_with_profile(42)
↓
Check: user.role == 'Student'? Attach student_profile
Check: user.role == 'Lecturer'? Attach lecturer_profile
↓
Return: User object with profile
```

---

### Method: get_user_by_email(email)

**Purpose:** Retrieve user by email (case-insensitive).

**Parameters:**
- `email` (string, required) - User's email address

**Returns:**
- User object

**Business Logic:**
1. Convert email to lowercase
2. Call `user_repository.get_by_email(email)`
3. Return user

**Exceptions:**
- `UserNotFoundError` if email doesn't exist

**Validation:**
- Email format validation (handled by EmailField)
- Case-insensitive lookup

---

### Method: update_user(user_id, update_data)

**Purpose:** Update user information (name, email, etc.).

**Parameters:**
- `user_id` (int, required) - User to update
- `update_data` (dict, required) - Fields to update
  - `first_name` (string, optional)
  - `last_name` (string, optional)
  - `email` (string, optional)

**Returns:**
- Updated User object

**Business Logic:**
1. Validate user exists: `user_repository.get_by_id(user_id)`
2. If updating email, check uniqueness: `user_repository.exists_by_email(new_email)`
3. Call `user_repository.update(user_id, update_data)`
4. Return updated user

**Exceptions:**
- `UserNotFoundError` if user doesn't exist
- `EmailAlreadyExistsError` if new email is taken

**Validation:**
- Email uniqueness (if email is being updated)
- Email format
- Name fields not empty

**Transaction:** Not required (single table update)

---

### Method: activate_user(user_id)

**Purpose:** Activate a deactivated user account.

**Parameters:**
- `user_id` (int, required) - User to activate

**Returns:**
- Updated User object with `is_active=True`

**Business Logic:**
1. Validate user exists
2. Set `is_active = True`
3. Update user in database
4. Log activation event
5. Return updated user

**Exceptions:**
- `UserNotFoundError` if user doesn't exist

**Authorization:**
- Only Admin can activate users

---

### Method: deactivate_user(user_id)

**Purpose:** Deactivate user account (soft delete). If user is lecturer, deactivate all their sessions.

**Parameters:**
- `user_id` (int, required) - User to deactivate

**Returns:**
- Updated User object with `is_active=False`

**Business Logic:**
1. Validate user exists
2. Check user role
3. If role == 'Lecturer':
   - Get all lecturer's sessions (cross-context call)
   - Deactivate all sessions
4. Set `is_active = False`
5. Update user in database
6. Log deactivation event
7. Return updated user

**Exceptions:**
- `UserNotFoundError` if user doesn't exist

**Transaction:** Required (user update + session deactivation)

**Cross-Context Integration:**
- Call Session Management context to deactivate lecturer's sessions

**Authorization:**
- Only Admin can deactivate users

---

## 1.3 UserService Validation Rules

**Email Validation:**
- Valid email format
- Unique across all users (case-insensitive)
- Cannot be empty

**Name Validation:**
- first_name and last_name required
- Minimum 2 characters each
- Maximum 50 characters each

**Role Validation:**
- Must be one of: 'Admin', 'Lecturer', 'Student'
- Cannot be changed after creation

---

## 1.4 UserService Error Handling

**Custom Exceptions to Define:**
- `UserNotFoundError` - User with given ID doesn't exist
- `EmailAlreadyExistsError` - Email is already registered
- `UserInactiveError` - User is deactivated

**Repository Exception Mapping:**
- `User.DoesNotExist` → `UserNotFoundError`
- `IntegrityError` (duplicate email) → `EmailAlreadyExistsError`

---

## 1.5 UserService Testing Checklist

- [ ] Get user by valid ID returns user
- [ ] Get user by invalid ID raises UserNotFoundError
- [ ] Get user by email (case-insensitive) works
- [ ] Update user with valid data succeeds
- [ ] Update user with duplicate email raises error
- [ ] Activate user sets is_active=True
- [ ] Deactivate user sets is_active=False
- [ ] Deactivate lecturer also deactivates sessions

---

# PART 2: AUTHENTICATION SERVICE

## 2.1 AuthenticationService Overview

**Purpose:** Handles user authentication, JWT token generation, and token validation.

**File:** `services/authentication_service.py`

**Dependencies:**
- UserRepository (fetch user by email)
- PasswordService (verify password)
- JWT library (PyJWT)

**Responsibilities:**
- Login (email + password for Admin/Lecturer)
- Generate JWT access and refresh tokens
- Validate JWT tokens
- Refresh access tokens
- Logout (token invalidation - optional)
- Generate passwordless JWT for students (email links)

---

## 2.2 AuthenticationService Methods

### Method: login(email, password)

**Purpose:** Authenticate user and return JWT tokens.

**Parameters:**
- `email` (string, required) - User's email
- `password` (string, required) - Plain text password

**Returns:**
- Dictionary:
  ```python
  {
      'access_token': 'eyJhbGc...',
      'refresh_token': 'eyJhbGc...',
      'user': {
          'user_id': 42,
          'email': 'john@example.com',
          'role': 'Lecturer',
          'full_name': 'John Doe'
      }
  }
  ```

**Business Logic:**
1. Convert email to lowercase
2. Get user by email: `user_repository.find_by_email(email)`
3. If user not found → raise `InvalidCredentialsError`
4. If user is Student (password is NULL) → raise `StudentCannotLoginError`
5. Verify password: `password_service.verify_password(password, user.password)`
6. If password invalid → raise `InvalidCredentialsError`
7. If user.is_active == False → raise `UserInactiveError`
8. Generate access token (15 min expiry)
9. Generate refresh token (7 days expiry)
10. Log successful login
11. Return tokens + user info

**Exceptions:**
- `InvalidCredentialsError` - Wrong email or password
- `StudentCannotLoginError` - Students use passwordless auth
- `UserInactiveError` - Account is deactivated

**Security:**
- Password verification using bcrypt/Argon2
- Constant-time comparison to prevent timing attacks
- Rate limiting (implement in API layer)

**Validation:**
- Email format
- Password not empty
- User has password (not NULL)

---

### Method: generate_access_token(user)

**Purpose:** Generate short-lived JWT access token.

**Parameters:**
- `user` (User object, required) - Authenticated user

**Returns:**
- JWT access token (string)

**Token Payload:**
```python
{
    'user_id': user.user_id,
    'email': user.email,
    'role': user.role,
    'exp': datetime.utcnow() + timedelta(minutes=15),  # Expiry
    'iat': datetime.utcnow(),  # Issued at
    'type': 'access'
}
```

**Business Logic:**
1. Create payload with user info
2. Set expiry time (15 minutes from now)
3. Sign with SECRET_KEY using HS256 algorithm
4. Return JWT string

**Security:**
- Use strong SECRET_KEY (from environment variable)
- Short expiry time (15 minutes)
- Include token type ('access')

---

### Method: generate_refresh_token(user)

**Purpose:** Generate long-lived JWT refresh token.

**Parameters:**
- `user` (User object, required) - Authenticated user

**Returns:**
- JWT refresh token (string)

**Token Payload:**
```python
{
    'user_id': user.user_id,
    'exp': datetime.utcnow() + timedelta(days=7),  # Expiry
    'iat': datetime.utcnow(),
    'type': 'refresh'
}
```

**Business Logic:**
1. Create payload with minimal user info (only user_id)
2. Set expiry time (7 days from now)
3. Sign with SECRET_KEY
4. Return JWT string

**Security:**
- Longer expiry (7 days)
- Minimal payload (only user_id)
- Can only be used to get new access tokens

---

### Method: validate_token(token, token_type='access')

**Purpose:** Validate and decode JWT token.

**Parameters:**
- `token` (string, required) - JWT token
- `token_type` (string, optional) - 'access' or 'refresh'

**Returns:**
- Decoded payload (dict) if valid

**Business Logic:**
1. Decode token using SECRET_KEY
2. Check token type matches expected type
3. Check expiry time (exp)
4. Return decoded payload

**Exceptions:**
- `InvalidTokenError` - Token is malformed
- `ExpiredTokenError` - Token has expired
- `InvalidTokenTypeError` - Wrong token type

**Security:**
- Verify signature
- Check expiry
- Validate token type

---

### Method: refresh_access_token(refresh_token)

**Purpose:** Generate new access token using refresh token.

**Parameters:**
- `refresh_token` (string, required) - Valid refresh token

**Returns:**
- New access token (string)

**Business Logic:**
1. Validate refresh token: `validate_token(refresh_token, token_type='refresh')`
2. Extract user_id from payload
3. Get user: `user_repository.get_by_id(user_id)`
4. Check user is active
5. Generate new access token
6. Return new access token

**Exceptions:**
- `InvalidTokenError` / `ExpiredTokenError` - Invalid refresh token
- `UserNotFoundError` - User doesn't exist
- `UserInactiveError` - User is deactivated

---

### Method: generate_student_attendance_token(student_profile_id, session_id)

**Purpose:** Generate JWT token for student to mark attendance via email link.

**Parameters:**
- `student_profile_id` (int, required) - Student's profile ID
- `session_id` (int, required) - Session ID for attendance

**Returns:**
- JWT token (string)

**Token Payload:**
```python
{
    'student_profile_id': student_profile_id,
    'session_id': session_id,
    'exp': datetime.utcnow() + timedelta(hours=2),  # 2 hour expiry
    'type': 'attendance'
}
```

**Business Logic:**
1. Validate student exists: `student_repository.exists_by_id(student_profile_id)`
2. Create payload with student_profile_id and session_id
3. Set short expiry (2 hours)
4. Sign with SECRET_KEY
5. Return JWT string

**Security:**
- Short expiry (2 hours - session duration)
- Specific to one student and one session
- Cannot be reused for other sessions

---

## 2.3 AuthenticationService Security Considerations

**Password Security:**
- Never store plain text passwords
- Use bcrypt or Argon2 for hashing
- Use strong salt (automatically handled by bcrypt/Argon2)

**JWT Token Security:**
- Use HS256 algorithm (symmetric)
- Strong SECRET_KEY (from environment, never hardcode)
- Short expiry for access tokens
- Store refresh tokens securely (HTTP-only cookies recommended)

**Rate Limiting:**
- Limit login attempts per IP (implement in API layer)
- Lock account after 5 failed attempts
- Unlock after 30 minutes or admin intervention

**Timing Attack Prevention:**
- Use constant-time comparison for password verification
- Don't reveal if email exists vs password wrong

---

## 2.4 AuthenticationService Error Handling

**Custom Exceptions:**
- `InvalidCredentialsError` - Wrong email or password
- `StudentCannotLoginError` - Students cannot use password login
- `InvalidTokenError` - Malformed JWT
- `ExpiredTokenError` - JWT has expired
- `InvalidTokenTypeError` - Wrong token type (access vs refresh)
- `UserInactiveError` - Account deactivated

**Error Messages (for API):**
- "Invalid credentials" (don't specify if email or password is wrong)
- "Students cannot log in with password. Please use the email link provided."
- "Your account has been deactivated. Contact admin."
- "Token has expired. Please log in again."

---

## 2.5 AuthenticationService Testing Checklist

- [ ] Login with valid credentials returns tokens
- [ ] Login with invalid email raises InvalidCredentialsError
- [ ] Login with invalid password raises InvalidCredentialsError
- [ ] Student login with password raises StudentCannotLoginError
- [ ] Login with inactive user raises UserInactiveError
- [ ] Generate access token returns valid JWT
- [ ] Generate refresh token returns valid JWT
- [ ] Validate valid access token succeeds
- [ ] Validate expired token raises ExpiredTokenError
- [ ] Refresh access token with valid refresh token succeeds
- [ ] Generate student attendance token returns valid JWT

---

# PART 3: PASSWORD SERVICE

## 3.1 PasswordService Overview

**Purpose:** Handles all password-related operations (hashing, verification, validation, reset).

**File:** `services/password_service.py`

**Dependencies:**
- bcrypt or Argon2 library
- UserRepository (update password)

**Responsibilities:**
- Hash passwords
- Verify passwords
- Validate password strength
- Generate password reset tokens
- Reset passwords

---

## 3.2 PasswordService Methods

### Method: hash_password(plain_password)

**Purpose:** Hash plain text password for secure storage.

**Parameters:**
- `plain_password` (string, required) - Plain text password

**Returns:**
- Hashed password (string)

**Business Logic:**
1. Validate password strength (call `validate_password_strength`)
2. Generate salt (automatic with bcrypt)
3. Hash password using bcrypt with cost factor 12
4. Return hashed password

**Algorithm:**
- Use bcrypt (recommended) or Argon2
- Cost factor: 12 (good balance of security and performance)

**Example:**
```
Input: "SecurePass123!"
↓
bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12))
↓
Output: "$2b$12$KIXnKq3Y5Z..."
```

---

### Method: verify_password(plain_password, hashed_password)

**Purpose:** Verify plain password against hashed password.

**Parameters:**
- `plain_password` (string, required) - Plain text password from login
- `hashed_password` (string, required) - Hashed password from database

**Returns:**
- Boolean (True if match, False otherwise)

**Business Logic:**
1. Use bcrypt.checkpw() to compare
2. Return result (True/False)

**Security:**
- Constant-time comparison (prevents timing attacks)
- bcrypt handles this automatically

---

### Method: validate_password_strength(password)

**Purpose:** Validate password meets complexity requirements.

**Parameters:**
- `password` (string, required) - Password to validate

**Returns:**
- Boolean (True if valid)

**Raises:**
- `WeakPasswordError` with specific reason if invalid

**Password Requirements:**
1. Minimum 8 characters
2. At least one uppercase letter (A-Z)
3. At least one lowercase letter (a-z)
4. At least one digit (0-9)
5. At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)

**Business Logic:**
1. Check length >= 8
2. Check has uppercase: `re.search(r'[A-Z]', password)`
3. Check has lowercase: `re.search(r'[a-z]', password)`
4. Check has digit: `re.search(r'[0-9]', password)`
5. Check has special char: `re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password)`
6. If any check fails, raise `WeakPasswordError` with specific message

**Error Messages:**
- "Password must be at least 8 characters long"
- "Password must contain at least one uppercase letter"
- "Password must contain at least one lowercase letter"
- "Password must contain at least one digit"
- "Password must contain at least one special character"

---

### Method: change_password(user_id, old_password, new_password)

**Purpose:** Change user's password (requires old password verification).

**Parameters:**
- `user_id` (int, required) - User changing password
- `old_password` (string, required) - Current password
- `new_password` (string, required) - New password

**Returns:**
- Success message

**Business Logic:**
1. Get user: `user_repository.get_by_id(user_id)`
2. If user.password is NULL (Student) → raise `StudentCannotHavePasswordError`
3. Verify old password: `verify_password(old_password, user.password)`
4. If verification fails → raise `InvalidPasswordError`
5. Validate new password strength
6. Hash new password
7. Update user: `user_repository.update_password(user_id, hashed_password)`
8. Log password change
9. Return success

**Exceptions:**
- `UserNotFoundError` - User doesn't exist
- `StudentCannotHavePasswordError` - Students don't have passwords
- `InvalidPasswordError` - Old password is wrong
- `WeakPasswordError` - New password doesn't meet requirements

**Validation:**
- Old password must be correct
- New password must be different from old
- New password must meet strength requirements

---

### Method: generate_reset_token(user_id)

**Purpose:** Generate secure token for password reset.

**Parameters:**
- `user_id` (int, required) - User requesting reset

**Returns:**
- Reset token (string)

**Token Format:**
- JWT with payload:
  ```python
  {
      'user_id': user_id,
      'exp': datetime.utcnow() + timedelta(hours=1),  # 1 hour expiry
      'type': 'password_reset'
  }
  ```

**Business Logic:**
1. Validate user exists and has password
2. Generate JWT token with 1 hour expiry
3. Log reset request
4. Return token (to be sent via email)

**Security:**
- Short expiry (1 hour)
- One-time use (invalidate after reset)
- Sent only to user's registered email

---

### Method: reset_password(reset_token, new_password)

**Purpose:** Reset password using reset token (no old password required).

**Parameters:**
- `reset_token` (string, required) - Valid reset token
- `new_password` (string, required) - New password

**Returns:**
- Success message

**Business Logic:**
1. Validate and decode reset token
2. Extract user_id from token
3. Check token hasn't been used (optional: maintain used tokens list)
4. Get user: `user_repository.get_by_id(user_id)`
5. Validate new password strength
6. Hash new password
7. Update user password
8. Invalidate reset token (mark as used)
9. Log password reset
10. Return success

**Exceptions:**
- `InvalidTokenError` / `ExpiredTokenError` - Invalid reset token
- `UserNotFoundError` - User doesn't exist
- `WeakPasswordError` - New password doesn't meet requirements
- `TokenAlreadyUsedError` - Reset token already used

**Transaction:** Not required (single update)

---

## 3.3 PasswordService Validation Rules

**Password Strength Rules:**
- Minimum 8 characters
- Must contain uppercase letter
- Must contain lowercase letter
- Must contain digit
- Must contain special character
- Cannot be same as old password (for change)

**Password Storage Rules:**
- Never store plain text
- Always hash with bcrypt/Argon2
- NULL for students only

---

## 3.4 PasswordService Security Considerations

**Hashing Algorithm:**
- Use bcrypt (recommended for Django)
- Argon2 is also acceptable (more secure but slower)
- Never use MD5, SHA1, or plain SHA256 (too fast, vulnerable to brute force)

**Salt:**
- Automatically generated by bcrypt per password
- Random, unique for each password
- Stored in the hash itself

**Cost Factor:**
- bcrypt: 12 (default, good balance)
- Higher = more secure but slower
- Lower = faster but less secure

**Timing Attacks:**
- bcrypt.checkpw() uses constant-time comparison
- Prevents attackers from guessing passwords based on response time

---

## 3.5 PasswordService Error Handling

**Custom Exceptions:**
- `WeakPasswordError` - Password doesn't meet requirements
- `InvalidPasswordError` - Old password is wrong
- `StudentCannotHavePasswordError` - Students don't use passwords
- `TokenAlreadyUsedError` - Reset token already used

---

## 3.6 PasswordService Testing Checklist

- [ ] Hash password returns bcrypt hash
- [ ] Verify correct password returns True
- [ ] Verify wrong password returns False
- [ ] Validate strong password passes
- [ ] Validate weak password (too short) raises error
- [ ] Validate password without uppercase raises error
- [ ] Change password with correct old password succeeds
- [ ] Change password with wrong old password raises error
- [ ] Change password for student raises error
- [ ] Generate reset token returns valid JWT
- [ ] Reset password with valid token succeeds
- [ ] Reset password with expired token raises error

---

# PART 4: REGISTRATION SERVICE

## 4.1 RegistrationService Overview

**Purpose:** Handles user registration for all roles (Admin, Lecturer, Student) with role-specific logic.

**File:** `services/registration_service.py`

**Dependencies:**
- UserRepository
- StudentProfileRepository
- LecturerProfileRepository
- PasswordService (hash passwords)
- Email Service (send welcome emails - cross-context)

**Responsibilities:**
- Register lecturers (self-registration, auto-activate)
- Register students (admin only, no password, set qr_code_data)
- Register admins (by existing admin)
- Validate registration data
- Create user + profile atomically
- Send welcome emails

---

## 4.2 RegistrationService Methods

### Method: register_lecturer(lecturer_data)

**Purpose:** Self-registration for lecturers with auto-activation.

**Parameters:**
- `lecturer_data` (dict, required):
  ```python
  {
      'first_name': 'John',
      'last_name': 'Doe',
      'email': 'john.doe@university.edu',
      'password': 'SecurePass123!',
      'department_name': 'Computer Science'
  }
  ```

**Returns:**
- Dictionary:
  ```python
  {
      'user': User object,
      'lecturer_profile': LecturerProfile object,
      'access_token': 'eyJhbGc...',
      'refresh_token': 'eyJhbGc...'
  }
  ```

**Business Logic:**
1. **Validate email uniqueness**: `user_repository.exists_by_email(email)`
   - If exists → raise `EmailAlreadyExistsError`
2. **Validate password strength**: `password_service.validate_password_strength(password)`
3. **Hash password**: `hashed_password = password_service.hash_password(password)`
4. **Start transaction** (`@transaction.atomic`)
5. **Create User**:
   ```python
   user_data = {
       'first_name': lecturer_data['first_name'],
       'last_name': lecturer_data['last_name'],
       'email': lecturer_data['email'].lower(),
       'password': hashed_password,
       'role': 'Lecturer',
       'is_active': True  # Auto-activate
   }
   user = user_repository.create(user_data)
   ```
6. **Create LecturerProfile**:
   ```python
   profile_data = {
       'user': user,
       'department_name': lecturer_data['department_name']
   }
   lecturer_profile = lecturer_repository.create(profile_data)
   ```
7. **Generate tokens**: `authentication_service.login(email, password)`
8. **Send welcome email** (async, outside transaction)
9. **Log registration event**
10. **Return** user, profile, and tokens

**Exceptions:**
- `EmailAlreadyExistsError` - Email is taken
- `WeakPasswordError` - Password doesn't meet requirements
- `ValidationError` - Invalid input data

**Transaction:** Required (User + LecturerProfile creation)

**Validation:**
- Email format and uniqueness
- Password strength
- first_name, last_name not empty
- department_name not empty (min 3 chars)

**Important Notes:**
- Lecturer is **auto-activated** (no admin approval needed)
- Can immediately create courses and sessions after registration
- Tokens returned so lecturer can login immediately

---

### Method: register_student(student_data, admin_user_id)

**Purpose:** Register student (admin only, no password, auto-set qr_code_data).

**Parameters:**
- `student_data` (dict, required):
  ```python
  {
      'student_id': 'BCS/234344',
      'first_name': 'Jane',
      'last_name': 'Smith',
      'email': 'jane.smith@university.edu',
      'program_id': 5,
      'stream_id': 2,  # Optional (NULL if program has no streams)
      'year_of_study': 2
  }
  ```
- `admin_user_id` (int, required) - Admin performing registration

**Returns:**
- Dictionary:
  ```python
  {
      'user': User object,
      'student_profile': StudentProfile object
  }
  ```

**Business Logic:**
1. **Validate admin user**: 
   - `admin = user_repository.get_by_id(admin_user_id)`
   - If `admin.role != 'Admin'` → raise `UnauthorizedError`
2. **Validate email uniqueness**: `user_repository.exists_by_email(email)`
3. **Validate student_id uniqueness**: `student_repository.exists_by_student_id(student_id)`
4. **Validate student_id format**: Match pattern `^[A-Z]{3}/[0-9]{6}$`
5. **Validate program exists**: Call Academic Structure context or check `program_repository.exists_by_id(program_id)`
6. **Validate stream logic**:
   - Get program: `program = program_repository.get_by_id(program_id)`
   - If `program.has_streams == True` and `stream_id is None` → raise `StreamRequiredError`
   - If `program.has_streams == False` and `stream_id is not None` → raise `StreamNotAllowedError`
   - If `stream_id` provided, validate stream belongs to program
7. **Start transaction** (`@transaction.atomic`)
8. **Create User**:
   ```python
   user_data = {
       'first_name': student_data['first_name'],
       'last_name': student_data['last_name'],
       'email': student_data['email'].lower(),
       'password': None,  # NULL for students
       'role': 'Student',
       'is_active': True
   }
   user = user_repository.create(user_data)
   ```
9. **Create StudentProfile**:
   ```python
   profile_data = {
       'user': user,
       'student_id': student_data['student_id'].upper(),
       'program_id': student_data['program_id'],
       'stream_id': student_data.get('stream_id'),  # Can be None
       'year_of_study': student_data['year_of_study'],
       'qr_code_data': student_data['student_id'].upper()  # Auto-set
   }
   student_profile = student_repository.create(profile_data)
   ```
10. **Send welcome email** (async, outside transaction)
11. **Log registration event**
12. **Return** user and profile

**Exceptions:**
- `UnauthorizedError` - Non-admin trying to register student
- `EmailAlreadyExistsError` - Email is taken
- `StudentIdAlreadyExistsError` - Student ID is taken
- `InvalidStudentIdFormatError` - Invalid student_id format
- `ProgramNotFoundError` - Program doesn't exist
- `StreamRequiredError` - Program has streams but stream_id not provided
- `StreamNotAllowedError` - Program has no streams but stream_id provided
- `StreamNotInProgramError` - Stream doesn't belong to program

**Transaction:** Required (User + StudentProfile creation)

**Validation:**
- Email format and uniqueness
- student_id format (`^[A-Z]{3}/[0-9]{6}$`) and uniqueness
- program_id exists
- stream_id validation based on program.has_streams
- year_of_study between 1 and 4

**Important Notes:**
- Student has **NO password** (password = NULL)
- `qr_code_data` is **auto-set to match student_id**
- `stream_id` can be NULL if program has no streams
- Only Admin can register students

---

### Method: register_admin(admin_data, creator_admin_id)

**Purpose:** Register new admin (by existing admin).

**Parameters:**
- `admin_data` (dict, required):
  ```python
  {
      'first_name': 'Alice',
      'last_name': 'Admin',
      'email': 'alice.admin@university.edu',
      'password': 'SecurePass123!'
  }
  ```
- `creator_admin_id` (int, required) - Existing admin creating new admin

**Returns:**
- User object (no profile for admin)

**Business Logic:**
1. **Validate creator is admin**:
   - `creator = user_repository.get_by_id(creator_admin_id)`
   - If `creator.role != 'Admin'` → raise `UnauthorizedError`
2. **Validate email uniqueness**
3. **Validate password strength**
4. **Hash password**
5. **Create User**:
   ```python
   user_data = {
       'first_name': admin_data['first_name'],
       'last_name': admin_data['last_name'],
       'email': admin_data['email'].lower(),
       'password': hashed_password,
       'role': 'Admin',
       'is_active': True
   }
   user = user_repository.create(user_data)
   ```
6. **Log admin creation event**
7. **Return** user

**Exceptions:**
- `UnauthorizedError` - Non-admin trying to create admin
- `EmailAlreadyExistsError` - Email is taken
- `WeakPasswordError` - Password doesn't meet requirements

**Transaction:** Not required (single User creation, no profile)

**Validation:**
- Email format and uniqueness
- Password strength
- first_name, last_name not empty

**Important Notes:**
- Admin has **NO profile extension** (no AdminProfile model)
- Only existing Admin can create new Admins

---

## 4.3 RegistrationService Validation Details

### Email Validation:
- **Format**: Valid email format (handled by EmailField)
- **Uniqueness**: Case-insensitive check across all users
- **Conversion**: Always convert to lowercase before saving

### Student ID Validation:
- **Format**: `^[A-Z]{3}/[0-9]{6}$` (e.g., BCS/234344)
- **Uniqueness**: Must be unique across all students
- **Conversion**: Always convert to uppercase before saving
- **QR Code**: `qr_code_data` must equal `student_id`

### Password Validation (Admin & Lecturer only):
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

### Stream Validation (Students only):
- If `program.has_streams == True`: `stream_id` is REQUIRED
- If `program.has_streams == False`: `stream_id` must be NULL
- If provided, `stream_id` must belong to `program_id`

### Department Validation (Lecturers only):
- Minimum 3 characters
- Maximum 100 characters
- Free text (no reference check against department table)

### Year of Study Validation (Students only):
- Must be integer between 1 and 4

---

## 4.4 RegistrationService Cross-Context Integration

**Academic Structure Context:**
- Validate `program_id` exists
- Get `program.has_streams` to determine stream requirement
- Validate `stream_id` exists and belongs to program

**Email Notification Context:**
- Send welcome email after successful registration
- Email should be sent **after transaction commits**
- Use async task queue (Celery) for email sending

**Integration Pattern:**
```python
# After successful registration (outside transaction)
email_data = {
    'recipient': user.email,
    'subject': 'Welcome to Attendance System',
    'template': 'welcome_lecturer.html' or 'welcome_student.html',
    'context': {
        'first_name': user.first_name,
        'role': user.role
    }
}
email_service.send_email(email_data)  # Async
```

---

## 4.5 RegistrationService Transaction Management

**When to Use Transactions:**
- ✅ Lecturer registration (User + LecturerProfile)
- ✅ Student registration (User + StudentProfile)
- ❌ Admin registration (only User, no profile)

**Transaction Pattern:**
```python
from django.db import transaction

@transaction.atomic
def register_lecturer(lecturer_data):
    # Step 1: Create User
    user = user_repository.create(user_data)
    
    # Step 2: Create LecturerProfile
    lecturer_profile = lecturer_repository.create({
        'user': user,
        'department_name': lecturer_data['department_name']
    })
    
    # If any step fails, both are rolled back
    return user, lecturer_profile

# Step 3: Send email (OUTSIDE transaction)
email_service.send_welcome_email(user.email)
```

**Why Email Outside Transaction:**
- Email sending can fail without affecting registration
- Retry email separately if it fails
- Don't hold database locks while sending email

---

## 4.6 RegistrationService Error Handling

**Custom Exceptions:**
- `EmailAlreadyExistsError` - Email is already registered
- `StudentIdAlreadyExistsError` - Student ID is already registered
- `InvalidStudentIdFormatError` - Student ID doesn't match pattern
- `WeakPasswordError` - Password doesn't meet requirements
- `ProgramNotFoundError` - Program doesn't exist
- `StreamRequiredError` - Stream required but not provided
- `StreamNotAllowedError` - Stream provided but program has no streams
- `StreamNotInProgramError` - Stream doesn't belong to program
- `UnauthorizedError` - Non-admin trying to register student/admin

**Error Messages (for API):**
- "Email address is already registered"
- "Student ID is already registered"
- "Invalid student ID format. Expected: ABC/123456"
- "Password must be at least 8 characters with uppercase, lowercase, digit, and special character"
- "Program not found"
- "Stream is required for this program"
- "This program does not have streams"
- "Stream does not belong to this program"
- "Only administrators can register students"

---

## 4.7 RegistrationService Testing Checklist

**Lecturer Registration:**
- [ ] Register with valid data succeeds
- [ ] Register with duplicate email raises error
- [ ] Register with weak password raises error
- [ ] User and profile created in transaction
- [ ] Lecturer is auto-activated
- [ ] Tokens returned on success
- [ ] Welcome email sent

**Student Registration:**
- [ ] Register with valid data succeeds
- [ ] Register by non-admin raises UnauthorizedError
- [ ] Register with duplicate email raises error
- [ ] Register with duplicate student_id raises error
- [ ] Register with invalid student_id format raises error
- [ ] Register with invalid program raises error
- [ ] Stream required if program has streams
- [ ] Stream not allowed if program has no streams
- [ ] qr_code_data auto-set to student_id
- [ ] User has NULL password
- [ ] User and profile created in transaction
- [ ] Welcome email sent

**Admin Registration:**
- [ ] Register with valid data succeeds
- [ ] Register by non-admin raises UnauthorizedError
- [ ] Register with duplicate email raises error
- [ ] Register with weak password raises error
- [ ] No profile created for admin

---

# PART 5: PROFILE SERVICE

## 5.1 ProfileService Overview

**Purpose:** Handles profile-specific operations (get, update) for StudentProfile and LecturerProfile.

**File:** `services/profile_service.py`

**Dependencies:**
- StudentProfileRepository
- LecturerProfileRepository
- UserRepository

**Responsibilities:**
- Get student profile with full info
- Get lecturer profile with full info
- Update student profile (year, stream)
- Update lecturer profile (department)
- Validate profile updates

---

## 5.2 ProfileService Methods

### Method: get_student_profile(student_profile_id)

**Purpose:** Get student profile with user, program, and stream information.

**Parameters:**
- `student_profile_id` (int, required) - Student profile ID

**Returns:**
- StudentProfile object with related data

**Business Logic:**
1. Get profile with relations: 
   ```python
   student_repository.get_with_full_info(student_profile_id)
   # Uses select_related('user', 'program', 'stream')
   ```
2. Return profile

**Exceptions:**
- `StudentNotFoundError` - Profile doesn't exist

---

### Method: get_student_profile_by_user_id(user_id)

**Purpose:** Get student profile by user ID.

**Parameters:**
- `user_id` (int, required) - User ID

**Returns:**
- StudentProfile object

**Business Logic:**
1. Get profile: `student_repository.get_by_user_id(user_id)`
2. Return profile

**Exceptions:**
- `StudentNotFoundError` - Profile doesn't exist for this user

---

### Method: get_student_profile_by_student_id(student_id)

**Purpose:** Get student profile by institutional student ID.

**Parameters:**
- `student_id` (string, required) - Institutional ID (e.g., BCS/234344)

**Returns:**
- StudentProfile object

**Business Logic:**
1. Convert student_id to uppercase
2. Get profile: `student_repository.get_by_student_id(student_id)`
3. Return profile

**Exceptions:**
- `StudentNotFoundError` - Profile doesn't exist

---

### Method: update_student_profile(student_profile_id, update_data)

**Purpose:** Update student profile information.

**Parameters:**
- `student_profile_id` (int, required) - Profile to update
- `update_data` (dict, required):
  ```python
  {
      'year_of_study': 3,  # Optional
      'stream_id': 5       # Optional
  }
  ```

**Returns:**
- Updated StudentProfile object

**Business Logic:**
1. Get existing profile: `student_repository.get_by_id(student_profile_id)`
2. If updating `stream_id`:
   - Get program: `profile.program`
   - If `program.has_streams == False` and `stream_id is not None` → raise `StreamNotAllowedError`
   - If `program.has_streams == True` and `stream_id is None` → raise `StreamRequiredError`
   - If `stream_id` provided, validate it belongs to program
3. If updating `year_of_study`:
   - Validate range (1-4)
4. Update profile: `student_repository.update(student_profile_id, update_data)`
5. Return updated profile

**Exceptions:**
- `StudentNotFoundError` - Profile doesn't exist
- `StreamNotAllowedError` - Program has no streams
- `StreamRequiredError` - Program requires stream
- `StreamNotInProgramError` - Stream doesn't belong to program
- `InvalidYearError` - Year not in range 1-4

**Validation:**
- year_of_study between 1 and 4
- stream_id validation based on program.has_streams
- Cannot update student_id or qr_code_data

**Transaction:** Not required (single table update)

---

### Method: get_lecturer_profile(lecturer_id)

**Purpose:** Get lecturer profile with user information.

**Parameters:**
- `lecturer_id` (int, required) - Lecturer profile ID

**Returns:**
- LecturerProfile object with related data

**Business Logic:**
1. Get profile with user: 
   ```python
   lecturer_repository.get_with_user(lecturer_id)
   # Uses select_related('user')
   ```
2. Return profile

**Exceptions:**
- `LecturerNotFoundError` - Profile doesn't exist

---

### Method: get_lecturer_profile_by_user_id(user_id)

**Purpose:** Get lecturer profile by user ID.

**Parameters:**
- `user_id` (int, required) - User ID

**Returns:**
- LecturerProfile object

**Business Logic:**
1. Get profile: `lecturer_repository.get_by_user_id(user_id)`
2. Return profile

**Exceptions:**
- `LecturerNotFoundError` - Profile doesn't exist for this user

---

### Method: update_lecturer_profile(lecturer_id, update_data)

**Purpose:** Update lecturer profile information.

**Parameters:**
- `lecturer_id` (int, required) - Profile to update
- `update_data` (dict, required):
  ```python
  {
      'department_name': 'Software Engineering'
  }
  ```

**Returns:**
- Updated LecturerProfile object

**Business Logic:**
1. Validate profile exists: `lecturer_repository.get_by_id(lecturer_id)`
2. Validate department_name (min 3 chars, max 100 chars)
3. Update profile: `lecturer_repository.update(lecturer_id, update_data)`
4. Return updated profile

**Exceptions:**
- `LecturerNotFoundError` - Profile doesn't exist
- `ValidationError` - Invalid department name

**Validation:**
- department_name not empty
- department_name min 3 characters

**Transaction:** Not required (single table update)

---

## 5.3 ProfileService Validation Rules

**Student Profile Updates:**
- year_of_study: Must be 1, 2, 3, or 4
- stream_id: Depends on program.has_streams
- Cannot update: student_id, qr_code_data, user_id, program_id

**Lecturer Profile Updates:**
- department_name: Min 3 chars, max 100 chars
- Cannot update: user_id

---

## 5.4 ProfileService Error Handling

**Custom Exceptions:**
- `StudentNotFoundError` - Student profile doesn't exist
- `LecturerNotFoundError` - Lecturer profile doesn't exist
- `StreamNotAllowedError` - Program has no streams
- `StreamRequiredError` - Program requires stream
- `StreamNotInProgramError` - Stream doesn't belong to program
- `InvalidYearError` - Year not in range 1-4

---

## 5.5 ProfileService Testing Checklist

- [ ] Get student profile by ID returns profile
- [ ] Get student profile by invalid ID raises error
- [ ] Get student profile by user_id works
- [ ] Get student profile by student_id works
- [ ] Update year of study succeeds
- [ ] Update stream for program with streams succeeds
- [ ] Update stream for program without streams raises error
- [ ] Update year out of range raises error
- [ ] Get lecturer profile by ID returns profile
- [ ] Get lecturer profile by user_id works
- [ ] Update department name succeeds
- [ ] Update with empty department name raises error

---

## Summary

This guide is now organized into **5 main parts**, each covering a specific service with all related information:

1. **UserService** - User retrieval, updates, activation/deactivation
2. **AuthenticationService** - Login, JWT tokens, token validation
3. **PasswordService** - Hashing, verification, strength validation, reset
4. **RegistrationService** - Lecturer, student, admin registration with role-specific logic
5. **ProfileService** - Profile retrieval and updates

Each service section includes:
- Overview and file location
- Detailed method specifications
- Business logic flows
- Validation rules
- Error handling
- Testing checklist
- Transaction management (where applicable)
- Cross-context integration (where applicable)

---

**Status**: 📋 Complete service specification ready for implementation