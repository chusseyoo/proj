# repositories_guide.md

This file provides a comprehensive guide for implementing the repository (data access) layer for User Management. It outlines repository structure, method specifications, query patterns, error handling, and integration points with other contexts.

---

## 1. Repository Class Structure

**Purpose**: Define the organization and naming of repository classes in the Django app.

### What to Include:
- **Repository Classes**: Create separate repository classes for each model (UserRepository, StudentProfileRepository, LecturerProfileRepository)
- **File Organization**: Place repositories in `user_management/repositories.py` or split into separate files in `user_management/repositories/` folder
- **Class Responsibilities**: Each repository handles data access for one model only
- **Naming Convention**: `{Model}Repository` (e.g., UserRepository)
- **Inheritance**: Optionally create a base repository class with common CRUD methods

### Notes:
- Keep repositories focused on data access only (no business logic)
- Repositories should be instantiated by the service layer
- Use dependency injection to pass repositories to services

---

## 2. Method Categories

**Purpose**: Organize repository methods into logical categories for clarity and maintainability.

### Categories:
- **CRUD Operations**: Basic create, read, update, delete methods
- **Query Methods**: Filtering, searching, and complex lookups
- **Existence Checks**: Fast boolean checks for entity existence
- **Bulk Operations**: Create/update/delete multiple records efficiently
- **Aggregation Methods**: Count, sum, average, and statistical queries

### Notes:
- Each category serves a specific purpose in the data access layer
- Methods should be atomic (do one thing well)
- Use descriptive names that indicate what the method does

---

## 3. Detailed Method Specifications

**Purpose**: Provide clear specifications for each repository method to ensure consistency.

### For Each Method, Specify:
- **Method Name**: Clear, descriptive name following naming conventions
- **Parameters**: All required and optional parameters with type hints
- **Return Type**: What the method returns (object, queryset, boolean, None)
- **Exceptions**: What exceptions to raise (DoesNotExist, ValidationError, IntegrityError)
- **Not Found Behavior**: Return None, empty queryset, or raise exception
- **Optimization**: Whether to use select_related/prefetch_related

### Example Specification:
```
Method: get_user_by_email(email: str) -> User
Parameters: email (string, required, case-insensitive)
Returns: User object
Raises: User.DoesNotExist if not found
Optimization: No related objects needed
```

---

## 4. User Repository Methods

**Purpose**: Handle all data access operations for the User model.

### Methods to Implement:

**Basic Retrieval:**
- `get_by_id(user_id)` - Get user by primary key, raise DoesNotExist if not found
- `find_by_id(user_id)` - Get user by primary key, return None if not found
- `get_by_email(email)` - Get user by email (case-insensitive), raise DoesNotExist if not found
- `find_by_email(email)` - Get user by email, return None if not found

**Filtering:**
- `list_by_role(role)` - Get all users with specific role (returns queryset)
- `list_active()` - Get all active users (is_active=True)
- `list_inactive()` - Get all inactive users (is_active=False)
- `list_active_by_role(role)` - Get active users with specific role

**Existence Checks:**
- `exists_by_email(email)` - Check if email exists (case-insensitive), return boolean
- `exists_by_id(user_id)` - Check if user_id exists, return boolean

**Creation:**
- `create(data)` - Create new user, return User instance
- `create_with_profile(user_data, profile_data, role)` - Create user and associated profile atomically

**Updates:**
- `update(user_id, data)` - Update user fields, return updated User instance
- `update_password(user_id, hashed_password)` - Update password field only
- `activate(user_id)` - Set is_active=True
- `deactivate(user_id)` - Set is_active=False (soft delete)

**Deletion:**
- `delete(user_id)` - Hard delete user (cascades to profiles)

**Optimized Queries:**
- `get_with_profile(user_id)` - Get user with student/lecturer profile (select_related)

### Notes:
- Email lookups should always be case-insensitive (use `email__iexact`)
- Password field can be NULL for students
- Soft delete (deactivate) is preferred over hard delete

---

## 5. StudentProfile Repository Methods

**Purpose**: Handle all data access operations for the StudentProfile model.

### Methods to Implement:

**Basic Retrieval:**
- `get_by_id(student_profile_id)` - Get by primary key, raise DoesNotExist if not found
- `get_by_user_id(user_id)` - Get student profile for a user, raise DoesNotExist if not found
- `get_by_student_id(student_id)` - Get by institutional ID (e.g., BCS/234344), raise DoesNotExist if not found
- `find_by_user_id(user_id)` - Get by user_id, return None if not found
- `find_by_student_id(student_id)` - Get by student_id, return None if not found

**Filtering:**
- `list_by_program(program_id)` - Get all students in a program
- `list_by_stream(stream_id)` - Get all students in a stream
- `list_by_year(year_of_study)` - Get all students in a specific year
- `list_by_program_and_stream(program_id, stream_id)` - Get students in program and stream
- `list_by_program_and_year(program_id, year_of_study)` - Get students in program and year

**Existence Checks:**
- `exists_by_student_id(student_id)` - Check if institutional student_id exists
- `exists_by_user_id(user_id)` - Check if student profile exists for user

**Creation:**
- `create(data)` - Create student profile, return StudentProfile instance
- `create_with_user(student_data, user_data)` - Create user and student profile atomically

**Updates:**
- `update(student_profile_id, data)` - Update student profile fields
- `update_year(student_profile_id, year_of_study)` - Update year only
- `update_stream(student_profile_id, stream_id)` - Update stream (can be NULL)

**Deletion:**
- `delete(student_profile_id)` - Delete student profile (cascades delete user if configured)

**Optimized Queries:**
- `get_with_user(student_profile_id)` - Get profile with user info (select_related)
- `get_with_full_info(student_profile_id)` - Get profile with user, program, and stream (select_related)
- `list_with_user_info(filters)` - Get multiple students with user info

### Notes:
- student_id must match format `^[A-Z]{3}/[0-9]{6}$`
- stream field can be NULL if program has no streams
- qr_code_data must equal student_id

---

## 6. LecturerProfile Repository Methods

**Purpose**: Handle all data access operations for the LecturerProfile model.

### Methods to Implement:

**Basic Retrieval:**
- `get_by_id(lecturer_id)` - Get by primary key, raise DoesNotExist if not found
- `get_by_user_id(user_id)` - Get lecturer profile for a user, raise DoesNotExist if not found
- `find_by_user_id(user_id)` - Get by user_id, return None if not found

**Filtering:**
- `list_by_department(department_name)` - Get all lecturers in a department
- `list_all()` - Get all lecturer profiles

**Existence Checks:**
- `exists_by_user_id(user_id)` - Check if lecturer profile exists for user

**Creation:**
- `create(data)` - Create lecturer profile, return LecturerProfile instance
- `create_with_user(lecturer_data, user_data)` - Create user and lecturer profile atomically

**Updates:**
- `update(lecturer_id, data)` - Update lecturer profile fields
- `update_department(lecturer_id, department_name)` - Update department only

**Deletion:**
- `delete(lecturer_id)` - Delete lecturer profile (cascades delete user if configured)

**Optimized Queries:**
- `get_with_user(lecturer_id)` - Get profile with user info (select_related)
- `list_with_user_info()` - Get all lecturers with user info

### Notes:
- Lecturer profiles are auto-created when lecturers self-register
- department_name is free text (no validation against department table)

---

## 7. Query Optimization Guidelines

**Purpose**: Ensure repository queries are performant and avoid common pitfalls like N+1 queries.

### Techniques:

**select_related():**
- Use for one-to-one and foreign key relationships
- Performs SQL JOIN to fetch related objects in one query
- Example: `StudentProfile.objects.select_related('user', 'program', 'stream')`
- Use when you know you'll access the related object

**prefetch_related():**
- Use for many-to-many and reverse foreign key relationships
- Performs separate queries and does the joining in Python
- Example: `Program.objects.prefetch_related('students')`
- Use when accessing multiple related objects

**only() and defer():**
- `only()`: Load only specified fields (exclude others)
- `defer()`: Load all fields except specified ones
- Use when you need partial model data
- Example: `User.objects.only('email', 'first_name')`

**Avoiding N+1 Queries:**
- Always use select_related/prefetch_related when accessing related objects in loops
- Use Django Debug Toolbar to identify N+1 queries
- Profile queries in development

**Index Usage:**
- Ensure indexes exist on frequently queried fields (email, student_id, role)
- Use `db_index=True` in model field definitions
- Create composite indexes for multi-field queries

### Notes:
- Optimization should be based on actual query patterns
- Don't over-optimize (premature optimization is bad)
- Measure query performance before and after optimization

---

## 8. Error Handling

**Purpose**: Define how to handle errors consistently across all repository methods.

### Error Types:

**DoesNotExist Exception:**
- Raised when `get()` method finds no matching record
- Handle in service layer or let it bubble up to view layer
- Methods prefixed with `get_` should raise this exception
- Methods prefixed with `find_` should return None instead

**MultipleObjectsReturned Exception:**
- Raised when `get()` method finds multiple records
- Usually indicates data integrity issue
- Log and investigate when this occurs
- Consider using `filter().first()` if multiple results are acceptable

**IntegrityError:**
- Raised on database constraint violations (unique, foreign key, check constraints)
- Example: Duplicate email, invalid student_id format
- Catch and convert to custom exceptions in service layer
- Common scenarios: email exists, student_id exists, invalid foreign key

**ValidationError:**
- Raised by model's `clean()` method or field validators
- Example: Invalid student_id format, password for student
- Handle before attempting database save

**Custom Exceptions:**
- Create custom exceptions for domain-specific errors
- Examples: UserNotFound, StudentNotFound, InvalidStudentId, EmailAlreadyExists
- Raise in repository, handle in service layer

### Error Handling Patterns:

**Get vs Find:**
- `get_*` methods: Raise DoesNotExist if not found
- `find_*` methods: Return None if not found

**Existence Checks First:**
- Use `exists()` before `get()` if not found is expected
- Example: `if repository.exists_by_email(email): raise EmailAlreadyExists()`

**Transaction Rollback:**
- Use `@transaction.atomic` for multi-model operations
- Rollback automatically on any exception

### Notes:
- Log all errors for debugging
- Provide meaningful error messages
- Don't expose raw database errors to API clients

---

## 9. Transaction Management

**Purpose**: Ensure data consistency when operations span multiple models or tables.

### When to Use Transactions:

**Multi-Model Creation:**
- Creating User + StudentProfile atomically
- Creating User + LecturerProfile atomically
- If user creation fails, profile should not be created (and vice versa)

**Multi-Step Updates:**
- Updating user and profile in same operation
- Deactivating user and all related sessions

**Bulk Operations:**
- Creating multiple students at once
- Updating multiple records

### How to Implement:

**Using @transaction.atomic Decorator:**
- Wrap repository methods that perform multiple database operations
- Example: `@transaction.atomic def create_with_profile(...)`
- Automatic rollback on any exception

**Using transaction.atomic() Context Manager:**
- For more granular control
- Can be used in service layer instead of repository

**Savepoints:**
- Use for nested transactions
- Allows partial rollback

### Rollback Scenarios:

**Automatic Rollback:**
- Any unhandled exception inside atomic block
- IntegrityError, ValidationError, DoesNotExist

**Manual Rollback:**
- Use `transaction.set_rollback(True)` to force rollback
- Useful for validation that happens after database operations

### Notes:
- Keep transactions short (performance)
- Don't perform external API calls inside transactions
- Database locks held during transaction

---

## 10. Filtering and Searching

**Purpose**: Provide flexible query capabilities for various search and filter scenarios.

### Filter Types:

**Exact Match:**
- `filter(role='Student')` - Exact match
- `filter(student_id='BCS/234344')` - Exact student ID
- `filter(is_active=True)` - Boolean filter

**Case-Insensitive Match:**
- `filter(email__iexact='john@example.com')` - Case-insensitive email
- Use for all email lookups

**Partial Match:**
- `filter(first_name__icontains='john')` - Case-insensitive contains
- `filter(last_name__startswith='Doe')` - Starts with
- `filter(student_id__startswith='BCS')` - Student IDs starting with BCS

**Pattern Match:**
- `filter(student_id__regex=r'^[A-Z]{3}/[0-9]{6}$')` - Regex match
- Use for validating student_id format

**NULL Checks:**
- `filter(password__isnull=True)` - Find students (no password)
- `filter(stream__isnull=False)` - Students with streams

**Range Filters:**
- `filter(year_of_study__gte=2)` - Year 2 or above
- `filter(date_joined__range=(start, end))` - Date range

**Combining Filters:**
- `filter(role='Student', is_active=True)` - AND condition
- `filter(Q(role='Student') | Q(role='Lecturer'))` - OR condition

### Search Implementation:

**Multi-Field Search:**
- Search across first_name, last_name, email
- Use Q objects to combine conditions
- Example: `filter(Q(first_name__icontains=query) | Q(last_name__icontains=query))`

**Student ID Search:**
- Support partial student_id search
- Example: Search for "BCS/234" returns all matching students

### Notes:
- Always use case-insensitive for text searches
- Index fields that are frequently filtered
- Use `Q` objects for complex OR conditions

---

## 11. Nullable Field Handling

**Purpose**: Properly handle fields that can be NULL in the database.

### Nullable Fields in User Management:

**User.password:**
- NULL for students (passwordless authentication)
- NOT NULL for admin and lecturer
- Filter students: `filter(password__isnull=True)`
- Filter admin/lecturer: `filter(password__isnull=False)`

**StudentProfile.stream:**
- NULL if program has no streams
- NOT NULL if program has streams
- Filter students without stream: `filter(stream__isnull=True)`
- Filter students with stream: `filter(stream__isnull=False)`

### Handling NULL in Queries:

**Filtering:**
- Use `__isnull=True` for NULL checks
- Use `__isnull=False` for NOT NULL checks
- Example: `StudentProfile.objects.filter(stream__isnull=True)`

**Updating to NULL:**
- Set field to None: `student.stream = None`
- Django converts None to NULL in database

**Validation:**
- Check if field is None before accessing related object
- Example: `if student.stream is not None: print(student.stream.stream_name)`

**Default Values vs NULL:**
- NULL means "no value" or "not applicable"
- Default values are set at creation time
- Example: `is_active` defaults to True (not NULL)

### Notes:
- Always check for None before accessing nullable foreign keys
- Document which fields can be NULL and why
- Use clean() method to enforce NULL constraints based on business rules

---

## 12. Cross-Context Integration

**Purpose**: Handle dependencies between User Management context and other bounded contexts.

### Dependencies:

**Academic Structure Context:**
- StudentProfile references Program (foreign key)
- StudentProfile references Stream (foreign key, nullable)
- Must validate program_id and stream_id exist before creating StudentProfile
- Must validate stream belongs to program

**Session Management Context:**
- Session references LecturerProfile (created by lecturer)
- Must validate lecturer exists and is active before creating session

**Attendance Recording Context:**
- Attendance references StudentProfile
- Must validate student exists and is active before marking attendance

**Email Notification Context:**
- Email notifications sent to User.email
- Must have valid email address for students

### Integration Patterns:

**Foreign Key References:**
- Use string references to avoid circular imports
- Example: `ForeignKey('academic_structure.Program')`
- Django resolves these at runtime

**Validation:**
- Validate foreign key IDs exist before saving
- Example: Check Program.objects.filter(program_id=id).exists()
- Raise ValidationError if invalid

**Accessing Related Data:**
- Use select_related() to fetch cross-context data efficiently
- Example: `student_profile = StudentProfile.objects.select_related('program', 'stream').get(...)`

**Avoiding Circular Imports:**
- Import models inside methods if needed
- Use `apps.get_model('app_label', 'ModelName')` for dynamic imports

### Notes:
- Keep cross-context calls minimal
- Use repository layer to encapsulate cross-context queries
- Document dependencies clearly

---

## 13. Pagination Support

**Purpose**: Efficiently handle large result sets by returning data in pages.

### Implementation:

**Django Paginator:**
- Use Django's built-in Paginator class
- Specify page size (e.g., 20, 50, 100)
- Return page object with results and metadata

**Repository Method Pattern:**
```
Method: list_users_paginated(page, page_size, filters)
Returns: Page object with:
  - results: list of User objects
  - total_count: total number of records
  - page_number: current page
  - total_pages: total number of pages
  - has_next: boolean
  - has_previous: boolean
```

**Offset/Limit Pattern:**
- Alternative to Paginator
- Use queryset slicing: `queryset[offset:offset+limit]`
- Calculate offset: `offset = (page - 1) * page_size`

### Recommendations:

**Default Page Size:**
- Users list: 20-50 per page
- Students list: 50-100 per page
- Reports: 100-500 per page

**Maximum Page Size:**
- Enforce maximum to prevent performance issues
- Example: max 1000 records per page

**Performance:**
- Use count() for total records (cached when possible)
- Use select_related() for paginated results with foreign keys
- Consider cursor-based pagination for very large datasets

### Notes:
- Implement pagination at repository level
- Return consistent pagination metadata
- Handle edge cases (page beyond range, empty results)

---

## 14. Common Query Patterns

**Purpose**: Document frequently used query patterns for consistency and reusability.

### User Queries:

**Get user by email (case-insensitive):**
- Pattern: `User.objects.filter(email__iexact=email).first()`
- Use case: Login, email verification

**Get all active users by role:**
- Pattern: `User.objects.filter(role=role, is_active=True)`
- Use case: List all active students, lecturers

**Check if email exists:**
- Pattern: `User.objects.filter(email__iexact=email).exists()`
- Use case: Registration validation

**Get user with profile:**
- Pattern: `User.objects.select_related('student_profile').get(user_id=id)`
- Use case: User profile page

### StudentProfile Queries:

**Get student with full info:**
- Pattern: `StudentProfile.objects.select_related('user', 'program', 'stream').get(...)`
- Use case: Student detail page, attendance marking

**Get all students in program:**
- Pattern: `StudentProfile.objects.filter(program=program_obj)`
- Use case: Enrollment lists, bulk email

**Get students in program and stream:**
- Pattern: `StudentProfile.objects.filter(program=program_obj, stream=stream_obj)`
- Use case: Session eligibility check

**Check if student_id exists:**
- Pattern: `StudentProfile.objects.filter(student_id=student_id).exists()`
- Use case: Registration validation

**Get students by year:**
- Pattern: `StudentProfile.objects.filter(year_of_study=year)`
- Use case: Year-level reports

### LecturerProfile Queries:

**Get lecturer by user email:**
- Pattern: `LecturerProfile.objects.select_related('user').get(user__email__iexact=email)`
- Use case: Lecturer lookup

**Get all lecturers in department:**
- Pattern: `LecturerProfile.objects.filter(department_name=dept)`
- Use case: Department statistics

### Count Queries:

**Count users by role:**
- Pattern: `User.objects.filter(role=role).count()`
- Use case: Dashboard statistics

**Count active students:**
- Pattern: `User.objects.filter(role='Student', is_active=True).count()`
- Use case: Reports

### Notes:
- Use these patterns consistently across the application
- Optimize with select_related/prefetch_related
- Add indexes for frequently filtered fields

---

## 15. Testing Guidelines

**Purpose**: Ensure repository methods work correctly through comprehensive testing.

### Test Categories:

**Unit Tests:**
- Test each repository method in isolation
- Use test database
- Mock external dependencies (cross-context calls)

**Integration Tests:**
- Test repository + database together
- Test cross-context queries
- Test transaction behavior

### What to Test:

**CRUD Operations:**
- Create: Record created with correct values
- Read: Correct record returned
- Update: Fields updated correctly
- Delete: Record removed from database

**Query Methods:**
- Filters return correct results
- Empty results handled properly
- Case-insensitive searches work
- Pagination works correctly

**Error Handling:**
- DoesNotExist raised when expected
- IntegrityError on duplicate email/student_id
- ValidationError on invalid data
- NULL constraint violations

**Edge Cases:**
- NULL values (password, stream)
- Empty strings vs NULL
- Very long strings (max_length)
- Special characters in text fields
- Multiple results when expecting one

**Performance:**
- N+1 query prevention
- select_related/prefetch_related usage
- Query count assertions

### Test Data Setup:

**Fixtures:**
- Use Django fixtures for complex test data
- JSON or YAML files

**Factories:**
- Use factory_boy for dynamic test data
- Example: UserFactory, StudentProfileFactory

**Test Database:**
- Use in-memory SQLite for speed
- Use PostgreSQL for production-like tests

### Test Organization:

**File Structure:**
- `tests/test_user_repository.py`
- `tests/test_student_profile_repository.py`
- `tests/test_lecturer_profile_repository.py`

**Test Naming:**
- `test_get_user_by_email_returns_user`
- `test_get_user_by_invalid_email_raises_does_not_exist`
- `test_create_student_profile_sets_qr_code_data`

### Notes:
- Aim for 80%+ code coverage
- Test happy path and error cases
- Use descriptive test names
- Clean up test data after each test

---

## 16. Performance Considerations

**Purpose**: Ensure repository operations are fast and scalable.

### Database Indexes:

**Indexed Fields:**
- User: email, role
- StudentProfile: student_id, user_id, program, stream
- LecturerProfile: user_id

**Composite Indexes:**
- StudentProfile: (program, stream)
- User: (role, is_active)

**Index Types:**
- B-tree for equality and range queries
- Hash for exact match only (PostgreSQL)

### Query Execution Time:

**Expected Times:**
- Simple get by ID: < 10ms
- Filter by indexed field: < 50ms
- Complex join (select_related): < 100ms
- Paginated list: < 200ms

**Slow Query Threshold:**
- Log queries > 500ms
- Investigate queries > 1000ms

### Caching Strategies:

**Model-Level Caching:**
- Cache frequently accessed, rarely changed data
- Example: User roles, program names
- Use Django's cache framework

**Query Result Caching:**
- Cache expensive queries
- Set appropriate TTL (time to live)
- Invalidate on updates

**When to Cache:**
- Static reference data
- Aggregation results
- User profile data

**When NOT to Cache:**
- Frequently changing data (attendance)
- User-specific sensitive data (passwords)
- Real-time data

### Bulk Operations:

**Bulk Create:**
- Use `bulk_create()` for creating multiple records
- Much faster than individual saves
- Example: Creating 100 students

**Bulk Update:**
- Use `update()` on queryset for mass updates
- Bypasses save() method (no signals)
- Example: Activating multiple users

**Bulk Delete:**
- Use `delete()` on queryset
- Cascades to related objects
- Use with caution

### Notes:
- Monitor slow queries in production
- Use Django Debug Toolbar in development
- Optimize based on actual usage patterns
- Don't over-optimize prematurely

---

## 17. Return Type Specifications

**Purpose**: Define consistent return types for repository methods to avoid confusion.

### Single Object Methods:

**get_* methods:**
- Return: Single model instance
- Not Found: Raise DoesNotExist exception
- Example: `get_by_id(user_id) -> User`

**find_* methods:**
- Return: Single model instance or None
- Not Found: Return None (no exception)
- Example: `find_by_email(email) -> User | None`

### List Methods:

**list_* methods:**
- Return: Django QuerySet (can be empty)
- Empty Results: Return empty queryset (not None)
- Example: `list_by_role(role) -> QuerySet[User]`

**Chaining:**
- QuerySets can be further filtered
- Example: `repository.list_active().filter(role='Student')`

### Boolean Methods:

**exists_* methods:**
- Return: Boolean (True/False)
- Never raises exceptions
- Example: `exists_by_email(email) -> bool`

### Create Methods:

**create_* methods:**
- Return: Created model instance
- Failure: Raise IntegrityError or ValidationError
- Example: `create(data) -> User`

### Update Methods:

**update_* methods:**
- Return: Updated model instance
- Not Found: Raise DoesNotExist
- Example: `update(user_id, data) -> User`

### Delete Methods:

**delete_* methods:**
- Return: None or number of deleted records
- Not Found: Raise DoesNotExist (hard delete) or return False (soft delete)
- Example: `delete(user_id) -> None`

**Soft Delete (deactivate):**
- Return: Updated User instance with is_active=False
- Example: `deactivate(user_id) -> User`

### Pagination Methods:

**Paginated List:**
- Return: Dictionary or Page object with metadata
- Keys: results, total_count, page_number, total_pages, has_next, has_previous
- Example: `list_paginated(page, size) -> dict`

### Notes:
- Use type hints in method signatures
- Document return types in docstrings
- Be consistent across all repositories

---

## 18. Method Naming Conventions

**Purpose**: Establish consistent naming for repository methods to improve readability and maintainability.

### Naming Patterns:

**get_* (Single Object, Raises Exception):**
- Gets a single object
- Raises DoesNotExist if not found
- Examples: `get_by_id`, `get_by_email`, `get_by_student_id`

**find_* (Single Object, Returns None):**
- Gets a single object
- Returns None if not found (no exception)
- Examples: `find_by_id`, `find_by_email`, `find_by_student_id`

**list_* (Multiple Objects, Returns QuerySet):**
- Gets multiple objects
- Returns QuerySet (can be empty)
- Examples: `list_all`, `list_by_role`, `list_active`, `list_by_program`

**exists_* (Boolean Check):**
- Checks if record exists
- Returns boolean
- Examples: `exists_by_email`, `exists_by_student_id`, `exists_by_id`

**create_* (Creates Record):**
- Creates new record
- Returns created instance
- Examples: `create`, `create_with_profile`, `create_bulk`

**update_* (Updates Record):**
- Updates existing record
- Returns updated instance
- Examples: `update`, `update_password`, `update_email`

**delete_* (Deletes Record):**
- Deletes record
- Returns None or deleted count
- Examples: `delete`, `delete_bulk`

**activate/deactivate (Soft Delete):**
- Changes is_active status
- Returns updated instance
- Examples: `activate`, `deactivate`

### Verb Guidelines:

- **get**: Retrieve single, expect to find
- **find**: Retrieve single, might not find
- **list**: Retrieve multiple
- **exists**: Boolean check
- **create**: Make new
- **update**: Change existing
- **delete**: Remove
- **activate/deactivate**: Toggle status

### Parameter Naming:

- Use full names: `user_id`, not `id`
- Use descriptive names: `filters`, `page_size`, `order_by`
- Boolean flags: `is_active`, `include_deleted`

### Notes:
- Stick to these conventions across all repositories
- Makes code self-documenting
- Easier for new developers to understand

---

## 19. Integration with Service Layer

**Purpose**: Define how repositories interact with the service layer.

### Service-Repository Relationship:

**Repository Responsibilities:**
- Data access only
- CRUD operations
- Query building
- Transaction management (when needed)

**Service Responsibilities:**
- Business logic
- Validation (business rules)
- Orchestrating multiple repository calls
- Error handling and conversion

### How Services Use Repositories:

**Dependency Injection:**
- Services receive repository instances via constructor
- Makes testing easier (mock repositories)
- Example: `UserService(user_repository, student_repository)`

**Multiple Repository Calls:**
- Service orchestrates calls to multiple repositories
- Example: Creating user + profile requires UserRepository and StudentProfileRepository
- Service handles transaction boundaries

**Transaction Boundaries:**
- Simple operations: Transaction in repository
- Complex operations: Transaction in service (spans multiple repositories)
- Use `@transaction.atomic` in service layer

### Example Flow:

**Register Student (Service Layer):**
1. Service validates business rules (student_id format, program exists)
2. Service calls UserRepository.create() to create user
3. Service calls StudentProfileRepository.create() to create profile
4. Service wraps both in transaction
5. Service returns success/error to API layer

### Error Handling:

**Repository Raises:**
- DoesNotExist
- IntegrityError
- ValidationError

**Service Catches and Converts:**
- DoesNotExist → Custom domain exception (UserNotFound)
- IntegrityError → Custom exception (EmailAlreadyExists, StudentIdExists)
- Returns meaningful errors to API layer

### Notes:
- Keep repositories thin (data access only)
- Put business logic in services
- Services orchestrate, repositories execute

---

## 20. Django ORM Best Practices

**Purpose**: Follow Django ORM best practices to write efficient, maintainable, and secure code.

### Best Practices:

**1. Avoid Raw SQL:**
- Use Django ORM for all queries
- Raw SQL is harder to maintain and database-specific
- Exception: Very complex queries that ORM can't handle efficiently

**2. Use F() Expressions:**
- For field-based updates
- Example: `User.objects.filter(user_id=1).update(login_count=F('login_count') + 1)`
- Prevents race conditions

**3. Use Q() Objects:**
- For complex OR conditions
- Example: `User.objects.filter(Q(role='Student') | Q(role='Lecturer'))`

**4. Avoid eval() and exec():**
- Never use with user input
- Security risk (code injection)

**5. Use get_or_create():**
- For idempotent creates
- Example: `User.objects.get_or_create(email=email, defaults={'first_name': 'John'})`
- Returns (object, created) tuple

**6. Use update_or_create():**
- For upsert operations
- Example: `User.objects.update_or_create(email=email, defaults={'first_name': 'John'})`

**7. Use select_for_update():**
- For row-level locking in concurrent scenarios
- Example: `User.objects.select_for_update().get(user_id=1)`
- Prevents race conditions

**8. Use only() and defer() Wisely:**
- `only()`: Load only specified fields
- `defer()`: Skip specified fields
- Useful for performance, but don't overuse

**9. Use iterator() for Large QuerySets:**
- Prevents loading all results into memory
- Example: `for user in User.objects.all().iterator(): ...`

**10. Use exists() Instead of count():**
- For boolean checks
- `exists()` is faster (stops at first match)
- Example: `if User.objects.filter(email=email).exists():`

**11. Use bulk_create() for Batch Inserts:**
- Much faster than individual saves
- Doesn't call save() or send signals
- Example: `User.objects.bulk_create([user1, user2, user3])`

**12. Use values() and values_list():**
- For retrieving specific fields only
- Returns dictionaries or tuples (not model instances)
- Example: `User.objects.values('email', 'first_name')`

**13. Avoid N+1 Queries:**
- Always use select_related/prefetch_related
- Use Django Debug Toolbar to detect
- Example: `StudentProfile.objects.select_related('user', 'program')`

**14. Use Database Constraints:**
- Enforce data integrity at database level
- Use Meta.constraints for Django 2.2+
- Example: UniqueConstraint, CheckConstraint

**15. Handle Timezone-Aware Datetimes:**
- Use Django's timezone utilities
- Store in UTC, display in user's timezone
- Example: `timezone.now()` instead of `datetime.now()`

### Security:

**SQL Injection Prevention:**
- Django ORM escapes all parameters automatically
- Never use string formatting for queries
- Never concatenate user input into queries

**Parameterized Queries:**
- Use placeholders: `User.objects.raw('SELECT * FROM users WHERE email = %s', [email])`
- Django handles escaping

### Notes:
- Follow Django documentation for latest best practices
- Use linters (pylint-django) to catch issues
- Review Django release notes for new ORM features

---

## Integration Points

**Used By:**
- Service layer for business logic operations
- API layer for direct data access (rare, prefer services)

**Calls:**
- Academic Structure repositories for program/stream validation
- Database via Django ORM

**Interacts With:**
- Django models (User, StudentProfile, LecturerProfile)
- Django ORM QuerySets
- Database (PostgreSQL)

---

## Summary Checklist

When implementing repositories, ensure:
- [ ] Separate repository class for each model
- [ ] Consistent naming conventions (get, find, list, exists, create, update, delete)
- [ ] Proper return types (object, queryset, boolean, None)
- [ ] Error handling (DoesNotExist, IntegrityError, ValidationError)
- [ ] Transaction management for multi-model operations
- [ ] Query optimization (select_related, prefetch_related)
- [ ] Nullable field handling (password, stream)
- [ ] Cross-context integration (program, stream references)
- [ ] Pagination support for list methods
- [ ] Comprehensive tests (unit + integration)
- [ ] Performance monitoring (query count, execution time)
- [ ] Documentation (docstrings for all methods)

---

**Status**: 📋 Complete repository specification ready for implementation