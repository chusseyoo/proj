# models_guide.md

Brief: Detailed specification for Django models in Academic Structure context. Defines Program, Stream, and Course models with all field specifications, relationships, constraints, model methods, and validation rules.

---

## Overview

Three Django models are required:
1. **Program** - Academic programs (degree programs)
2. **Stream** - Subdivisions within programs (optional, depends on program.has_streams)
3. **Course** - Individual courses offered in programs

---

## Model 1: Program

### Purpose
Represents academic degree programs (e.g., Bachelor of Computer Science). Programs can have streams (subdivisions) or not, controlled by the `has_streams` flag.

### Table Name
`programs`

### Fields Specification

| Field Name | Django Field Type | Parameters | Description |
|------------|------------------|------------|-------------|
| `program_id` | AutoField | `primary_key=True` | Auto-incrementing primary key |
| `program_name` | CharField | `max_length=200, unique=True, blank=False, null=False` | Full name of program |
| `program_code` | CharField | `max_length=3, unique=True, blank=False, null=False` | 3-letter abbreviation (e.g., BCS, ENG) |
| `department_name` | CharField | `max_length=50, blank=False, null=False` | Department offering program (5-50 chars) |
| `has_streams` | BooleanField | `default=False` | Whether program has stream subdivisions |

### Meta Options
- `db_table = 'programs'`
- `ordering = ['program_name']`
- `indexes`: 
  - Index on `program_code` (unique, but for performance)
  - Index on `department_name`

### Model Methods to Implement

**1. `__str__(self)`**
- Return: `f"{self.program_code} - {self.program_name}"`
- Example: "BCS - Bachelor of Computer Science"

**2. `can_be_deleted(self)`**
- Check if program can be safely deleted
- Return: `True` if no students enrolled AND no courses exist
- Logic:
  ```python
  has_students = self.students.exists()  # Reverse relation from StudentProfile
  has_courses = self.courses.exists()    # Reverse relation from Course
  return not (has_students or has_courses)
  ```

**3. `get_stream_count(self)`**
- Return: Number of streams in this program
- Logic: `return self.streams.count()`

**4. `requires_streams(self)`**
- Return: `self.has_streams`
- Convenience method for checking if streams are required

### Validation Rules (`clean()` method)

**1. Program Code Format Validation**
- Must be exactly 3 uppercase letters
- Use regex: `^[A-Z]{3}$`
- Raise `ValidationError` if format is invalid
- Message: "Program code must be exactly 3 uppercase letters (e.g., BCS, ENG)"

**2. Program Code Uniqueness**
- Django handles via `unique=True`
- Additional check in clean() for better error messages

**3. Program Name Validation**
- Minimum 5 characters
- Maximum 200 characters
- Cannot be empty

**4. Department Name Validation**
- Minimum 3 characters
- Cannot be empty

**5. has_streams Consistency (Post-Save Check)**
- If `has_streams = True`, at least one Stream should exist (warning, not error)
- If `has_streams = False`, no Streams should exist
- This is enforced more in service layer

### Save Override

**In `save()` method:**
1. Convert `program_code` to uppercase: `self.program_code = self.program_code.upper()`
2. Call `self.full_clean()` to run validation
3. Call `super().save(*args, **kwargs)`

### Custom Validators

**Create a custom validator function for program_code:**
```python
def validate_program_code_format(value):
    import re
    pattern = r'^[A-Z]{3}$'
    if not re.match(pattern, value):
        raise ValidationError('Program code must be exactly 3 uppercase letters')
```
- Add to `program_code` field validators parameter

### Database Constraints

**CHECK Constraints:**
- `program_code` matches regex `^[A-Z]{3}$`
- `program_name` length >= 5
- `department_name` length >= 5 and <= 50

**UNIQUE Constraints:**
- `program_code` (enforced by field)
- `program_name` (enforced by field)

**Indexes:**
- Index on `program_code` (for student ID validation)
- Index on `department_name` (for filtering by department)

---

## Model 2: Stream

### Purpose
Represents subdivisions within programs (e.g., Stream A, Stream B). Only exists if parent Program has `has_streams = True`.

### Table Name
`streams`

### Fields Specification

| Field Name | Django Field Type | Parameters | Description |
|------------|------------------|------------|-------------|
| `stream_id` | AutoField | `primary_key=True` | Auto-incrementing primary key |
| `stream_name` | CharField | `max_length=100, blank=False, null=False` | Name of stream (e.g., Stream A, Morning Batch) |
| `program` | ForeignKey | `to=Program, on_delete=CASCADE, related_name='streams'` | Parent program |
| `year_of_study` | IntegerField | `validators=[MinValueValidator(1), MaxValueValidator(4)]` | Which year (1-4) |

### Meta Options
- `db_table = 'streams'`
- `ordering = ['program', 'year_of_study', 'stream_name']`
- `unique_together = [['program', 'stream_name', 'year_of_study']]`
  - Prevents duplicate stream names for same program/year
- `indexes`: 
  - Index on `program`
  - Index on `year_of_study`

### Model Methods to Implement

**1. `__str__(self)`**
- Return: `f"{self.program.program_code} Year {self.year_of_study} - {self.stream_name}"`
- Example: "BCS Year 2 - Stream A"

**2. `get_student_count(self)`**
- Return: Number of students in this stream
- Logic: `return self.students.count()`  # Reverse relation from StudentProfile

**3. `can_be_deleted(self)`**
- Check if stream can be safely deleted
- Return: `True` if no students assigned
- Logic: `return not self.students.exists()`

### Validation Rules (`clean()` method)

**1. Program has_streams Validation**
- Ensure parent program has `has_streams = True`
- Get program: `self.program`
- Check: `if not self.program.has_streams: raise ValidationError`
- Message: "Cannot create stream for program that does not have streams enabled"

**2. Year of Study Validation**
- Must be between 1 and 4
- Handled by validators, but double-check in clean()

**3. Stream Name Validation**
- Minimum 2 characters
- Cannot be empty

### Save Override

**In `save()` method:**
1. Call `self.full_clean()` to run validation
2. Call `super().save(*args, **kwargs)`

### Database Constraints

**CHECK Constraints:**
- `year_of_study BETWEEN 1 AND 4`

**UNIQUE Constraint:**
- Unique together: `(program, stream_name, year_of_study)`
- Prevents duplicate "Stream A" for BCS Year 2

**Foreign Key Constraints:**
- `program` → CASCADE delete (if program deleted, all streams deleted)

---

## Model 3: Course

### Purpose
Represents individual courses offered in programs (e.g., Data Structures, Database Systems). Each course belongs to one program and can have one assigned lecturer.

### Table Name
`courses`

### Fields Specification

| Field Name | Django Field Type | Parameters | Description |
|------------|------------------|------------|-------------|
| `course_id` | AutoField | `primary_key=True` | Auto-incrementing primary key |
| `course_name` | CharField | `max_length=200, blank=False, null=False` | Full name of course |
| `course_code` | CharField | `max_length=6, unique=True, blank=False, null=False` | 6-character alphanumeric code (e.g., BCS012, BEG230, DIT410) |
| `program` | ForeignKey | `to=Program, on_delete=CASCADE, related_name='courses'` | Program offering this course |
| `department_name` | CharField | `max_length=50, blank=False, null=False` | Department teaching course (5-50 chars) |
| `lecturer` | ForeignKey | `to='user_management.LecturerProfile', on_delete=SET_NULL, null=True, blank=True, related_name='courses'` | Assigned lecturer (NULLABLE) |

### Meta Options
- `db_table = 'courses'`
- `ordering = ['course_code']`
- `indexes`: 
  - Index on `course_code` (unique, but for performance)
  - Index on `program`
  - Index on `lecturer`

### Model Methods to Implement

**1. `__str__(self)`**
- Return: `f"{self.course_code} - {self.course_name}"`
- Example: "CS201 - Data Structures and Algorithms"

**2. `is_assigned_to_lecturer(self)`**
- Return: `self.lecturer is not None`
- Check if course has assigned lecturer

**3. `get_lecturer_name(self)`**
- Return: Lecturer's full name or "Not Assigned"
- Logic:
  ```python
  if self.lecturer:
      return self.lecturer.user.get_full_name()
  return "Not Assigned"
  ```

**4. `can_be_deleted(self)`**
- Check if course can be safely deleted
- Return: `True` if no sessions exist
- Logic: `return not self.sessions.exists()`  # Reverse relation from Session

### Validation Rules (`clean()` method)

**1. Course Code Format Validation**
- Pattern: 2-4 uppercase letters + 3 digits
- Use regex: `^[A-Z]{2,4}[0-9]{3}$`
- Raise `ValidationError` if format is invalid
- Message: "Course code must be 2-4 uppercase letters followed by 3 digits (e.g., CS201, ENG301)"

**2. Course Code Uniqueness**
- Django handles via `unique=True`

**3. Course Name Validation**
- Minimum 3 characters
- Maximum 200 characters

**4. Lecturer Active Validation**
- If `lecturer` is provided, check lecturer.user.is_active
- Raise `ValidationError` if lecturer is inactive
- Message: "Cannot assign inactive lecturer to course"

### Save Override

**In `save()` method:**
1. Convert `course_code` to uppercase: `self.course_code = self.course_code.upper()`
2. Call `self.full_clean()` to run validation
3. Call `super().save(*args, **kwargs)`

### Custom Validators

**Create a custom validator function for course_code:**
```python
def validate_course_code_format(value):
    import re
    pattern = r'^[A-Z0-9]{6}$'
    if not re.match(pattern, value):
        raise ValidationError('Course code must be exactly 6 uppercase alphanumeric characters (e.g., BCS012, BEG230, DIT410)')
```
- Add to `course_code` field validators parameter

### Database Constraints

**CHECK Constraints:**
- `course_code` matches regex `^[A-Z0-9]{6}$`

**UNIQUE Constraints:**
- `course_code` (enforced by field)

**Foreign Key Constraints:**
- `program` → CASCADE delete (if program deleted, courses deleted)
- `lecturer` → SET_NULL (if lecturer deleted, course remains but lecturer_id = NULL)

---

## Relationships Summary

### Program ↔ Stream (One-to-Many)
- **Program side**: Access via `program.streams.all()` (reverse relation)
- **Stream side**: Access via `stream.program`
- **Delete behavior**: CASCADE (deleting program deletes all streams)
- **Constraint**: Streams only exist if `program.has_streams = True`

### Program ↔ Course (One-to-Many)
- **Program side**: Access via `program.courses.all()` (reverse relation)
- **Course side**: Access via `course.program`
- **Delete behavior**: CASCADE (deleting program deletes all courses)

### Course ↔ LecturerProfile (Many-to-One, Optional)
- **Course side**: Access via `course.lecturer` (can be None)
- **LecturerProfile side**: Access via `lecturer_profile.courses.all()` (reverse relation)
- **Delete behavior**: SET_NULL (if lecturer deleted, course.lecturer = None)
- **Nullable**: Yes - course can exist without lecturer initially

### Program ↔ StudentProfile (One-to-Many, Cross-Context)
- **Program side**: Access via `program.students.all()` (reverse relation from User Management)
- **StudentProfile side**: Access via `student_profile.program`
- Cross-context relationship (defined in User Management context)

### Stream ↔ StudentProfile (One-to-Many, Cross-Context, Optional)
- **Stream side**: Access via `stream.students.all()` (reverse relation from User Management)
- **StudentProfile side**: Access via `student_profile.stream` (can be None)
- Cross-context relationship (defined in User Management context)

---

## Migration Considerations

### Migration Order
1. Create Program model first
2. Create Stream model (depends on Program)
3. Create Course model (depends on Program and LecturerProfile from User Management)
4. Add indexes and constraints

### Initial Data
- Create a few sample programs via data migration or admin
- Create streams if programs have `has_streams = True`
- Courses can be added later by admin

### Constraints to Add Post-Migration
- CHECK constraint for program_code format
- CHECK constraint for course_code format
- UNIQUE together constraint for streams

---

## Common Queries to Support

The models should efficiently support these queries:

1. **Get all programs in a department**
   - Filter: `Program.objects.filter(department_name='Computer Science')`

2. **Get programs with streams**
   - Filter: `Program.objects.filter(has_streams=True)`

3. **Get all streams for a program**
   - Query: `Stream.objects.filter(program=program_obj)`

4. **Get streams for specific year**
   - Query: `Stream.objects.filter(program=program_obj, year_of_study=2)`

5. **Get all courses in a program**
   - Query: `Course.objects.filter(program=program_obj)`

6. **Get courses taught by lecturer**
   - Query: `Course.objects.filter(lecturer=lecturer_obj)`

7. **Get courses without assigned lecturer**
   - Query: `Course.objects.filter(lecturer__isnull=True)`

8. **Check if course code exists**
   - Query: `Course.objects.filter(course_code='CS201').exists()`

---

## Important Notes

### Nullable Fields
- **Course.lecturer**: NULL if no lecturer assigned yet (must be set before creating sessions)
- **StudentProfile.stream** (cross-context): NULL if program has no streams

### Auto-Generated Fields
- **program_id, stream_id, course_id**: Auto-increment (don't set manually)

### Business Rules Enforced in Model
- Program code must match format `^[A-Z]{3}$`
- Course code must match format `^[A-Z]{2,4}[0-9]{3}$`
- Streams only for programs with `has_streams = True`
- Year of study between 1 and 4

### Business Rules Enforced in Service Layer
- Program cannot be deleted if students enrolled or courses exist
- Stream cannot be deleted if students assigned
- Course cannot be deleted if sessions exist
- Lecturer must be active when assigning to course
- Program with `has_streams = True` should have at least one stream (warning)

### Cross-Context Dependencies
- Course references `user_management.LecturerProfile`
- Use string reference in ForeignKey: `to='user_management.LecturerProfile'`
- Ensures models can be imported without circular dependencies

---

## Next Steps After Creating Models

1. Run `python manage.py makemigrations academic_structure`
2. Review the generated migration file
3. Run `python manage.py migrate`
4. Test models in Django shell
5. Create model tests in `tests/test_models.py`
6. Proceed to create repositories (data access layer)

---

**Status**: 📋 Complete model specification ready for implementation