# models_guide.md

This guide provides a detailed specification for Django models in the User Management context. It defines entity structure, field specifications, relationships, constraints, model methods, and validation rules - everything needed to clearly instruct an AI or developer on how to build these models.

---

## Overview

Three Django models are required:
1. **User** - Core user entity for all system users
2. **StudentProfile** - Extended profile for students (one-to-one with User)
3. **LecturerProfile** - Extended profile for lecturers (one-to-one with User)

---

## Model 1: User

### Purpose
Represents all system users (Admin, Lecturer, Student). This is the authentication model.

### Table Name
`users`

### Fields Specification

| Field Name | Django Field Type | Parameters | Description |
|------------|------------------|------------|-------------|
| `user_id` | AutoField | `primary_key=True` | Auto-incrementing primary key |
| `first_name` | CharField | `max_length=50, blank=False, null=False` | User's first name |
| `last_name` | CharField | `max_length=50, blank=False, null=False` | User's last name |
| `email` | EmailField | `max_length=255, unique=True, blank=False, null=False` | Unique email address |
| `password` | CharField | `max_length=255, blank=True, null=True` | Hashed password - **NULL for students** |
| `role` | CharField | `max_length=20, choices=ROLE_CHOICES, blank=False, null=False` | User role enum |
| `is_active` | BooleanField | `default=True` | Account active/deactivated status |
| `date_joined` | DateTimeField | `auto_now_add=True` | Account creation timestamp |

### Role Choices (Enum)
Define a choices tuple:
```
ROLE_CHOICES = [
    ('Admin', 'Admin'),
    ('Lecturer', 'Lecturer'),
    ('Student', 'Student'),
]
```

### Meta Options
- `db_table = 'users'`
- `ordering = ['email']`
- `indexes`: Create index on `email` and `role` fields

### Model Methods to Implement

**1. `__str__(self)`**
- Return: `f"{self.first_name} {self.last_name} ({self.email})"`

**2. `get_full_name(self)`**
- Return: `f"{self.first_name} {self.last_name}"`

**3. `is_student(self)`**
- Return: `self.role == 'Student'`

**4. `is_lecturer(self)`**
- Return: `self.role == 'Lecturer'`

**5. `is_admin(self)`**
- Return: `self.role == 'Admin'`

**6. `has_password(self)`**
- Return: `self.password is not None and self.password != ''`

### Properties to Implement

**1. `full_name` (read-only property)**
- Use `@property` decorator
- Return: `self.get_full_name()`

### Validation Rules (`clean()` method)

**1. Password Validation**
- If `role == 'Student'`, password MUST be NULL
- If `role in ['Admin', 'Lecturer']`, password MUST NOT be NULL
- Raise `ValidationError` if violated

**2. Email Validation**
- Ensure email is lowercase before saving
- Django's EmailField handles format validation

### Save Override

**In `save()` method:**
1. (Redundant if upstream passed a normalized Email value object) Ensure lowercase defensively: `self.email = self.email.lower()`
2. Call `self.full_clean()` to run validation
3. Call `super().save(*args, **kwargs)`

### Email Normalization Rationale

Email lowercasing is performed centrally by the domain `Email` value object at construction time. The model keeps a defensive lowercase assignment for safety, but service / use case layers should rely on the value object to guarantee normalization and format validation. This avoids duplicated logic and ensures all persisted emails are canonical before reaching the ORM.

### Database Constraints

**CHECK Constraints (define in Meta or use Django constraints):**
- Student role must have null password
- Admin/Lecturer roles must have non-null password

**Indexes:**
- Index on `email` (for login lookups)
- Index on `role` (for role filtering)

---

## Model 2: StudentProfile

### Purpose
Extended profile information for students. One-to-one relationship with User where role='Student'.

### Table Name
`student_profiles`

### Fields Specification

| Field Name | Django Field Type | Parameters | Description |
|------------|------------------|------------|-------------|
| `student_profile_id` | AutoField | `primary_key=True` | Auto-incrementing primary key |
| `student_id` | CharField | `max_length=20, unique=True, blank=False, null=False` | Institutional student ID (format: ABC/123456) |
| `user` | OneToOneField | `to=User, on_delete=CASCADE, related_name='student_profile'` | Link to User model |
| `program` | ForeignKey | `to='academic_structure.Program', on_delete=PROTECT, related_name='students'` | Student's program |
| `stream` | ForeignKey | `to='academic_structure.Stream', on_delete=SET_NULL, null=True, blank=True, related_name='students'` | Optional stream |
| `year_of_study` | IntegerField | `validators=[MinValueValidator(1), MaxValueValidator(4)]` | Current year (1-4) |
| `qr_code_data` | CharField | `max_length=20, blank=False, null=False` | QR code content (must equal student_id) |

### Meta Options
- `db_table = 'student_profiles'`
- `ordering = ['student_id']`
- `indexes`: 
  - Index on `student_id` (already unique, but for performance)
  - Index on `user_id`
  - Composite index on `(program, stream)`

### Model Methods to Implement

**1. `__str__(self)`**
- Return: `f"{self.student_id} - {self.user.get_full_name()}"`

**2. `get_program_code(self)`**
- Extract first 3 characters from student_id
- Return: `self.student_id[:3]`

**3. `validate_student_id_format(self)`**
- Check regex pattern: `^[A-Z]{3}/[0-9]{6}$`
- Return: `True/False`

### Validation Rules (`clean()` method)

**1. Student ID Format Validation**
- Use regex: `^[A-Z]{3}/[0-9]{6}$`
- Raise `ValidationError` if format is invalid
- Message: "Student ID must follow format: ABC/123456"

**2. QR Code Data Validation**
- `qr_code_data` MUST equal `student_id`
- Raise `ValidationError` if they don't match
- Message: "QR code data must match student ID"

**3. User Role Validation**
- Ensure `user.role == 'Student'`
- Raise `ValidationError` if user is not a student
- Message: "User must have Student role"

**4. Stream Validation**
- If program has streams (`program.has_streams == True`), stream MUST NOT be null
- If program has no streams (`program.has_streams == False`), stream MUST be null
- Raise `ValidationError` if violated

### Save Override

**In `save()` method:**
1. Auto-set `qr_code_data = self.student_id` if not provided (never manually supplied)
2. Convert `student_id` to uppercase for canonical storage
3. Call `self.full_clean()` to run validation
4. Call `super().save(*args, **kwargs)`

#### Rationale for Centralized Derivation
`qr_code_data` is a pure mirror of `student_id`. Deriving it inside the model and domain entity prevents duplication across services, serializers, management commands, and migrations. Only the canonical `student_id` is accepted as input; `qr_code_data` is always computed, ensuring any invariant (or database CHECK constraint) requiring `qr_code_data = student_id` cannot be violated upstream.

### Custom Validators

**Create a custom validator function:**
```
def validate_student_id_format(value):
    import re
    pattern = r'^[A-Z]{3}/[0-9]{6}$'
    if not re.match(pattern, value):
        raise ValidationError('Student ID must follow format: ABC/123456')
```
- Add to `student_id` field validators parameter

### Database Constraints

**CHECK Constraints:**
- `student_id` matches regex `^[A-Z]{3}/[0-9]{6}$`
- `qr_code_data = student_id`
- `year_of_study BETWEEN 1 AND 4`

**Foreign Key Constraints:**
- `user` → CASCADE delete (if user deleted, profile deleted)
- `program` → PROTECT (cannot delete program if students enrolled)
- `stream` → SET_NULL (if stream deleted, set to null)

---

## Model 3: LecturerProfile

### Purpose
Extended profile information for lecturers. One-to-one relationship with User where role='Lecturer'.

### Table Name
`lecturer_profiles`

### Fields Specification

| Field Name | Django Field Type | Parameters | Description |
|------------|------------------|------------|-------------|
| `lecturer_id` | AutoField | `primary_key=True` | Auto-incrementing primary key |
| `user` | OneToOneField | `to=User, on_delete=CASCADE, related_name='lecturer_profile'` | Link to User model |
| `department_name` | CharField | `max_length=100, blank=False, null=False` | Department/Faculty name |

### Meta Options
- `db_table = 'lecturer_profiles'`
- `ordering = ['department_name']`
- `indexes`: Index on `user_id`

### Model Methods to Implement

**1. `__str__(self)`**
- Return: `f"{self.user.get_full_name()} - {self.department_name}"`

### Validation Rules (`clean()` method)

**1. User Role Validation**
- Ensure `user.role == 'Lecturer'`
- Raise `ValidationError` if user is not a lecturer
- Message: "User must have Lecturer role"

### Database Constraints

**Foreign Key Constraints:**
- `user` → CASCADE delete (if user deleted, profile deleted)

---

## Relationships Summary

### User ↔ StudentProfile (One-to-One)
- **User side**: Access via `user.student_profile` (reverse relation)
- **StudentProfile side**: Access via `student_profile.user`
- **Delete behavior**: CASCADE (deleting user deletes student profile)
- **Constraint**: Only exists when `user.role == 'Student'`

### User ↔ LecturerProfile (One-to-One)
- **User side**: Access via `user.lecturer_profile` (reverse relation)
- **LecturerProfile side**: Access via `lecturer_profile.user`
- **Delete behavior**: CASCADE (deleting user deletes lecturer profile)
- **Constraint**: Only exists when `user.role == 'Lecturer'`

### StudentProfile → Program (Many-to-One)
- **StudentProfile side**: Access via `student_profile.program`
- **Program side**: Access via `program.students.all()` (reverse relation)
- **Delete behavior**: PROTECT (cannot delete program with enrolled students)

### StudentProfile → Stream (Many-to-One, Optional)
- **StudentProfile side**: Access via `student_profile.stream` (can be None)
- **Stream side**: Access via `stream.students.all()` (reverse relation)
- **Delete behavior**: SET_NULL (if stream deleted, set student.stream = None)
- **Nullable**: Yes - only required if program has streams

---

## Signals (Optional Implementation)

### Post-Save Signal for User Model

**Purpose**: Auto-create profile when user is created

**Trigger**: After User.save()

**Logic**:
1. If user is newly created (`created=True`)
2. If `user.role == 'Lecturer'`, create LecturerProfile
3. If `user.role == 'Student'`, create StudentProfile (only if student_id provided)

**Note**: Student profiles are typically created explicitly by admin, so signal may not be needed for students.

---

## Migration Considerations

### Migration Order
1. Create User model first
2. Create StudentProfile and LecturerProfile models (depend on User)
3. Add indexes and constraints

### Initial Data
- Create at least one Admin user via data migration or management command
- Admin credentials should be configurable via environment variables

### Constraints to Add Post-Migration
- CHECK constraint for student_id format (use Django 2.2+ constraints)
- CHECK constraint for qr_code_data = student_id
- CHECK constraint for year_of_study range

---

## Testing Checklist

### User Model Tests
- [ ] Create user with all roles (Admin, Lecturer, Student)
- [ ] Verify student cannot have password
- [ ] Verify admin/lecturer must have password
- [ ] Test email uniqueness
- [ ] Test email case-insensitivity
- [ ] Test is_active default value
- [ ] Test role validation
- [ ] Test get_full_name() method

### StudentProfile Model Tests
- [ ] Create student profile with valid student_id
- [ ] Test student_id format validation (valid/invalid patterns)
- [ ] Test qr_code_data auto-set to student_id
- [ ] Test qr_code_data must match student_id
- [ ] Test year_of_study range (1-4)
- [ ] Test user must have Student role
- [ ] Test stream required when program has streams
- [ ] Test stream must be null when program has no streams
- [ ] Test cascade delete (delete user → profile deleted)

### LecturerProfile Model Tests
- [ ] Create lecturer profile
- [ ] Test user must have Lecturer role
- [ ] Test cascade delete (delete user → profile deleted)
- [ ] Test department_name required

---

## Common Queries to Support

The models should efficiently support these queries:

1. **Get all active users by role**
   - Filter: `User.objects.filter(role='Student', is_active=True)`

2. **Get student profile with user info**
   - Use: `StudentProfile.objects.select_related('user')`

3. **Get all students in a program**
   - Filter: `StudentProfile.objects.filter(program_id=5)`

4. **Get all students in a specific stream**
   - Filter: `StudentProfile.objects.filter(stream_id=2)`

5. **Get lecturer by user email**
   - Query: `LecturerProfile.objects.select_related('user').get(user__email='...')`

6. **Check if student_id exists**
   - Query: `StudentProfile.objects.filter(student_id='BCS/234344').exists()`

---

## Important Notes

### Nullable Fields
- **User.password**: NULL for students (they use passwordless JWT auth)
- **StudentProfile.stream**: NULL if program has no streams

### Auto-Generated Fields
- **user_id, student_profile_id, lecturer_id**: Auto-increment (don't set manually)
- **date_joined**: Auto-set on creation
- **qr_code_data**: Auto-set to match student_id in save() method

### Business Rules Enforced in Model
- Students cannot have passwords
- Student ID must match format ABC/123456
- QR code data must equal student ID
- Stream required/optional based on program configuration

### Business Rules Enforced in Service Layer
- Email uniqueness (also at DB level)
- Password strength validation (in PasswordService)
- Program/Stream existence validation (when creating StudentProfile)

### Cross-Context Dependencies
- StudentProfile references `academic_structure.Program` and `academic_structure.Stream`
- Use string references in ForeignKey: `to='academic_structure.Program'`
- Ensures models can be imported without circular dependencies

---

## Next Steps After Creating Models

1. Run `python manage.py makemigrations user_management`
2. Review the generated migration file
3. Run `python manage.py migrate`
4. Test models in Django shell
5. Create model tests in `tests/test_models.py`
6. Proceed to create repositories (data access layer)

---

**Status**: 📋 Complete model specification ready for implementation