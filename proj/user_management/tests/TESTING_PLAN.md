# USER MANAGEMENT TESTING - LAYER-BY-LAYER ACTION PLAN

Following Academic Structure's approach but adapted for the Service Layer pattern.
Focus: Critical Path Testing (Option B) with systematic layer progression.

---

## PHASE 1: DOMAIN LAYER TESTS

- Goal: Test core business entities and value objects
- Location: `user_management/tests/domain/`
- Estimated Time: 4–6 hours

### Files to create

1. test_user_entity.py (~150 lines)
   - Test User entity instantiation
   - Test role validation (Admin, Lecturer, Student)
   - Test password invariants:
     - Students CANNOT have passwords
     - Admin/Lecturer MUST have passwords
   - Test user activation/deactivation
   - Test helper methods (is_student, is_lecturer, is_admin)
   - Test __str__ and full_name

2. test_student_profile_entity.py (~100 lines)
   - Test StudentProfile instantiation
   - Test year_of_study validation (1–4 only)
   - Test QR code data matches student_id
   - Test update_year() method with validation
   - Test update_stream() method
   - Test program_code extraction from student_id

3. test_lecturer_profile_entity.py (~50 lines)
   - Test LecturerProfile instantiation
   - Test department_name validation
   - Test basic properties

4. test_value_objects.py (~120 lines)
   - Email Value Object:
     - Test valid email formats
     - Test invalid email rejection
     - Test normalization (lowercase)
     - Test equality comparison
   - StudentId Value Object:
     - Test valid format (ABC/123456)
     - Test invalid format rejection
     - Test program_code extraction
     - Test normalization

5. test_domain_services.py (~80 lines)
   - IdentityService:
     - Test email normalization
   - EnrollmentService:
     - Test validate_stream_requirement (has_streams=True)
     - Test validate_stream_requirement (has_streams=False)
     - Test stream belongs to program validation

Total domain tests: ~500 lines, 5 files

Key testing patterns (from academic_structure):
- Use @pytest.mark.parametrize for multiple test cases
- Test both valid and invalid inputs
- Test business rule invariants
- Use pytest.raises for exception testing

Example structure:

```python
"""Tests for User entity."""
import pytest
from user_management.domain.entities import User, UserRole
from user_management.domain.value_objects import Email

class TestUserEntity:
    def test_create_valid_lecturer(self):
        user = User(
            user_id=1,
            first_name="John",
            last_name="Doe",
            email=Email("john@example.com"),
            role=UserRole.LECTURER,
            has_password=True
        )
        assert user.is_lecturer()

    def test_student_cannot_have_password(self):
        with pytest.raises(ValueError):
            User(
                user_id=1,
                first_name="Jane",
                last_name="Student",
                email=Email("jane@example.com"),
                role=UserRole.STUDENT,
                has_password=True  # Should fail!
            )
```

---

## PHASE 2: APPLICATION LAYER TESTS

- Goal: Test business logic in Services and Use Cases
- Location: `user_management/tests/application/`
- Estimated Time: 2–3 days

Note: User Management uses a Service Layer (not Use Cases like academic_structure), so we test Services directly (they contain the logic).

### Subdirectories

- services/
  - test_registration_service.py
  - test_authentication_service.py
  - test_password_service.py
  - test_user_service.py
- use_cases/
  - test_use_case_wrappers.py

### Files to create

1. services/test_registration_service.py (~400 lines) – HIGH PRIORITY

   A. register_lecturer() tests:
   - Test successful lecturer registration
   - Test email already exists → EmailAlreadyExistsError
   - Test weak password → WeakPasswordError
   - Test email normalization (JoHn@Test.com → john@test.com)
   - Test password hashing (not stored as plaintext)
   - Test profile creation
   - Test auto-login returns tokens
   - Test department_name validation

   B. register_student() tests:
   - Test successful student registration (by admin)
   - Test non-admin user → UnauthorizedError
   - Test email already exists → EmailAlreadyExistsError
   - Test student_id already exists → StudentIdAlreadyExistsError
   - Test invalid student_id format → InvalidStudentIdFormatError
   - Test program validation (must exist)
   - Test stream required when has_streams=True → StreamRequiredError
   - Test stream not allowed when has_streams=False → StreamNotAllowedError
   - Test stream belongs to program validation
   - Test year_of_study validation (1–4)
   - Test QR code generation

   C. register_admin() tests:
   - Test successful admin registration (by admin)
   - Test non-admin user → UnauthorizedError
   - Test email already exists
   - Test weak password

   Mocking strategy:
   - Mock UserRepository (create, exists_by_email)
   - Mock StudentProfileRepository (create, exists_by_student_id)
   - Mock LecturerProfileRepository (create)
   - Mock PasswordService (hash_password, validate_password_strength)
   - Mock AuthenticationService (login)
   - Use actual domain entities (no mocking)

2. services/test_authentication_service.py (~350 lines) – HIGH PRIORITY

   A. login() tests:
   - Test successful login (lecturer)
   - Test successful login (admin)
   - Test invalid email → InvalidCredentialsError
   - Test wrong password → InvalidCredentialsError
   - Test inactive user → UserInactiveError
   - Test student login attempt → StudentCannotLoginError
   - Test returns access_token and refresh_token
   - Test email normalization during login

   B. logout() tests:
   - Test successful logout
   - Test token blacklisting

   C. refresh_token() tests:
   - Test successful token refresh
   - Test invalid refresh token → InvalidTokenError
   - Test expired refresh token → ExpiredTokenError
   - Test returns new access_token

   D. verify_token() tests:
   - Test valid token
   - Test invalid token
   - Test expired token

3. services/test_password_service.py (~200 lines) – MEDIUM PRIORITY

   A. validate_password_strength() tests:
   - Test valid strong password
   - Test too short password → WeakPasswordError
   - Test no uppercase → WeakPasswordError
   - Test no lowercase → WeakPasswordError
   - Test no digits → WeakPasswordError
   - Test common passwords → WeakPasswordError

   B. hash_password() tests:
   - Test password is hashed (not plaintext)
   - Test same password produces different hashes (salt)
   - Test hash format is valid

   C. verify_password() tests:
   - Test correct password verification
   - Test incorrect password verification

   D. change_password() tests:
   - Test successful password change
   - Test old password verification
   - Test weak new password → WeakPasswordError
   - Test student cannot change password

4. services/test_user_service.py (~150 lines) – LOW PRIORITY

   - get_user_by_id() tests
   - get_user_by_email() tests
   - update_user() tests
   - deactivate_user() tests

5. use_cases/test_use_case_wrappers.py (~100 lines) – LOW PRIORITY

   - Test that use cases properly delegate to services

Total application tests: ~1,200 lines, 5 files

Example structure:

```python
"""Tests for RegistrationService."""
import pytest
from unittest.mock import Mock, patch

from user_management.application.services import RegistrationService
from user_management.domain.entities import User, UserRole
from user_management.domain.exceptions import EmailAlreadyExistsError

class TestRegistrationService:
    @pytest.fixture
    def mock_user_repo(self):
        return Mock()

    @pytest.fixture
    def mock_password_service(self):
        service = Mock()
        service.hash_password.return_value = "hashed_password_123"
        return service

    @pytest.fixture
    def registration_service(self, mock_user_repo, mock_password_service):
        return RegistrationService(
            user_repository=mock_user_repo,
            student_repository=Mock(),
            lecturer_repository=Mock(),
            password_service=mock_password_service,
            authentication_service=Mock()
        )

    def test_register_lecturer_success(self, registration_service, mock_user_repo):
        # Arrange
        mock_user_repo.exists_by_email.return_value = False
        mock_user_repo.create.return_value = User(...)

        # Act
        result = registration_service.register_lecturer({
            'email': 'john@example.com',
            'password': 'SecurePass123',
            'first_name': 'John',
            'last_name': 'Doe',
            'department_name': 'Computer Science'
        })

        # Assert
        assert result['user'].email == 'john@example.com'
        mock_user_repo.create.assert_called_once()
```

---

## PHASE 3: INFRASTRUCTURE LAYER TESTS

- Goal: Test repository implementations (DB interactions)
- Location: `user_management/tests/infrastructure/`
- Estimated Time: 4–6 hours

### Files to create

1. test_user_repository.py (~200 lines)
   - Test create() – creates User in DB
   - Test find_by_email() – retrieves by email
   - Test find_by_id() – retrieves by ID
   - Test exists_by_email() – checks existence
   - Test update() – updates user fields
   - Test delete() – removes user
   - Test domain→ORM mapping

2. test_student_profile_repository.py (~150 lines)
   - Test create() – creates StudentProfile
   - Test find_by_student_id()
   - Test exists_by_student_id()
   - Test update()
   - Test FK relationship to User

3. test_lecturer_profile_repository.py (~100 lines)
   - Test create() – creates LecturerProfile
   - Test find_by_user_id()
   - Test FK relationship to User

Total infrastructure tests: ~450 lines, 3 files

Note: These are integration tests using Django's test database. Use `@pytest.mark.django_db`.

Example structure:

```python
"""Tests for UserRepository."""
import pytest
from user_management.infrastructure.repositories import UserRepository
from user_management.domain.entities import User, UserRole
from user_management.domain.value_objects import Email

@pytest.mark.django_db
class TestUserRepository:
    @pytest.fixture
    def repository(self):
        return UserRepository()

    def test_create_user(self, repository):
        # Arrange
        user = User(
            user_id=None,
            first_name="John",
            last_name="Doe",
            email=Email("john@example.com"),
            role=UserRole.LECTURER,
            has_password=True
        )

        # Act
        created = repository.create(user, password_hash="hash123")

        # Assert
        assert created.user_id is not None
        assert created.email.value == "john@example.com"
```

---

## PHASE 4: INTERFACE LAYER (API) TESTS

- Goal: Test REST API endpoints end-to-end
- Location: `user_management/tests/interfaces/api/`
- Estimated Time: 1–2 days

### Files to create

1. conftest.py (~100 lines)
   - Shared fixtures:
     - api_client
     - admin_user (authenticated)
     - lecturer_user (authenticated)
     - student_user (authenticated)
     - sample_program/stream (from academic_structure)

2. test_registration_api.py (~400 lines) – HIGH PRIORITY

   A. POST /api/users/register/lecturer/
   - Test successful registration
   - Test returns tokens (access + refresh)
   - Test duplicate email → 409
   - Test weak password → 400
   - Test missing fields → 400
   - Test invalid email format → 400

   B. POST /api/users/register/student/
   - Test successful registration (as admin)
   - Test non-admin → 403
   - Test duplicate student_id → 409
   - Test invalid student_id format → 400
   - Test stream validation errors → 400
   - Test program validation → 404

   C. POST /api/users/register/admin/
   - Test successful registration (as admin)
   - Test non-admin → 403

3. test_authentication_api.py (~300 lines) – HIGH PRIORITY

   A. POST /api/users/login/
   - Test successful login (lecturer)
   - Test successful login (admin)
   - Test returns tokens
   - Test invalid credentials → 401
   - Test inactive user → 403
   - Test student login → 403
   - Test missing fields → 400

   B. POST /api/users/logout/
   - Test successful logout
   - Test unauthenticated → 401

   C. POST /api/users/token/refresh/
   - Test successful token refresh
   - Test invalid token → 401
   - Test expired token → 401

4. test_profile_api.py (~200 lines) – MEDIUM PRIORITY

   A. GET /api/users/profile/
   - Test retrieve own profile
   - Test unauthenticated → 401

   B. PATCH /api/users/profile/
   - Test update own profile
   - Test cannot update email
   - Test cannot update role

   C. POST /api/users/change-password/
   - Test successful password change
   - Test wrong old password → 400
   - Test student cannot change password → 403

5. test_permissions.py (~150 lines) – MEDIUM PRIORITY

   - Test IsAdmin permission class
   - Test IsOwnerOrAdmin permission class
   - Test authentication requirements

Total API tests: ~1,150 lines, 5 files

Example structure:

```python
"""Tests for Registration API endpoints."""
import pytest
from rest_framework import status
from rest_framework.test import APIClient

@pytest.mark.django_db
class TestRegistrationAPI:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    def test_register_lecturer_success(self, api_client):
        # Arrange
        url = '/api/users/register/lecturer/'
        data = {
            'email': 'john@example.com',
            'password': 'SecurePass123',
            'first_name': 'John',
            'last_name': 'Doe',
            'department_name': 'Computer Science'
        }

        # Act
        response = api_client.post(url, data, format='json')

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert 'access_token' in response.data
        assert 'refresh_token' in response.data
```

---

## SUMMARY: DELIVERABLES BY PHASE

PHASE 1 – DOMAIN (4–6 hours):
- 5 test files, ~500 lines
- Entities tested
- Value objects tested
- Domain services tested

PHASE 2 – APPLICATION (2–3 days):
- 5 test files, ~1,200 lines
- RegistrationService fully tested (HIGH PRIORITY)
- AuthenticationService fully tested (HIGH PRIORITY)
- PasswordService fully tested
- Other services covered

PHASE 3 – INFRASTRUCTURE (4–6 hours):
- 3 test files, ~450 lines
- All repositories tested
- DB interactions verified

PHASE 4 – API (1–2 days):
- 5 test files, ~1,150 lines
- Registration endpoints tested
- Authentication endpoints tested
- Profile endpoints tested
- Permissions tested

Total estimated:
- 18 test files
- ~3,300 lines of test code
- 5–7 days total effort
- Critical path covered (Option B)

---

## TESTING TOOLS & CONVENTIONS

Tools:
- pytest – test framework
- pytest-django – Django integration
- unittest.mock – mocking
- APIClient – DRF test client
- @pytest.mark.django_db – DB access

Conventions (from academic_structure):
- One test class per function/method
- Fixtures for reusable test data
- Descriptive test names (test_action_condition_expected)
- Arrange–Act–Assert pattern
- Use parametrize for multiple similar tests

---

## NEXT STEPS

1. Review this plan – make adjustments
2. Start Phase 1 (Domain tests)
3. Commit after each phase
4. Run tests continuously
5. Track coverage

Ready to start with Phase 1 (Domain Layer)?
