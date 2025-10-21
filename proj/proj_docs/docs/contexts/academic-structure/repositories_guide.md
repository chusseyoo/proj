# repositories_guide.md

Brief: Comprehensive guide for implementing the repository (data access) layer for Academic Structure. Defines repository classes, methods, query patterns, error handling, and integration with other contexts.

---

## File Organization

**Repository Layer Structure:**
```
academic_structure/
├── repositories/
│   ├── __init__.py
│   ├── program_repository.py   # ProgramRepository
│   ├── stream_repository.py    # StreamRepository
│   └── course_repository.py    # CourseRepository
├── models.py
└── ...
```

**Why Separate Files:**
- Each repository focused on one model
- Easier to test in isolation
- Clear dependencies
- Simpler navigation

---

# PART 1: PROGRAM REPOSITORY

## 1.1 ProgramRepository Overview

**Purpose:** Handles all data access operations for the Program model.

**File:** `repositories/program_repository.py`

**Dependencies:**
- Program model (from models.py)

**Responsibilities:**
- CRUD operations for programs
- Query programs by department
- Check if program code exists
- Get programs with/without streams
- Validate program can be deleted

---

## 1.2 ProgramRepository Methods

### Method: get_by_id(program_id)

**Purpose:** Retrieve program by primary key.

**Parameters:**
- `program_id` (int, required) - Program's primary key

**Returns:**
- Program object

**Raises:**
- `Program.DoesNotExist` if not found

**Query:**
```python
Program.objects.get(program_id=program_id)
```

---

### Method: find_by_id(program_id)

**Purpose:** Retrieve program by primary key, return None if not found.

**Parameters:**
- `program_id` (int, required)

**Returns:**
- Program object or None

**Query:**
```python
try:
    return Program.objects.get(program_id=program_id)
except Program.DoesNotExist:
    return None
```

---

### Method: get_by_code(program_code)

**Purpose:** Retrieve program by program code (e.g., "BCS").

**Parameters:**
- `program_code` (string, required) - 3-letter program code

**Returns:**
- Program object

**Raises:**
- `Program.DoesNotExist` if not found

**Query:**
```python
Program.objects.get(program_code=program_code.upper())
```

**Note:** Convert to uppercase before query

---

### Method: exists_by_code(program_code)

**Purpose:** Check if program code already exists.

**Parameters:**
- `program_code` (string, required)

**Returns:**
- Boolean (True if exists, False otherwise)

**Query:**
```python
Program.objects.filter(program_code=program_code.upper()).exists()
```

**Use Case:** Validation before creating new program

---

### Method: exists_by_id(program_id)

**Purpose:** Check if program exists by ID.

**Parameters:**
- `program_id` (int, required)

**Returns:**
- Boolean

**Query:**
```python
Program.objects.filter(program_id=program_id).exists()
```

---

### Method: list_all()

**Purpose:** Get all programs.

**Returns:**
- QuerySet of Program objects

**Query:**
```python
Program.objects.all().order_by('program_name')
```

---

### Method: list_by_department(department_name)

**Purpose:** Get all programs in a department.

**Parameters:**
- `department_name` (string, required)

**Returns:**
- QuerySet of Program objects

**Query:**
```python
Program.objects.filter(department_name=department_name).order_by('program_name')
```

---

### Method: list_with_streams()

**Purpose:** Get all programs that have streams enabled.

**Returns:**
- QuerySet of Program objects

**Query:**
```python
Program.objects.filter(has_streams=True).order_by('program_name')
```

**Use Case:** Listing programs where streams must be considered

---

### Method: list_without_streams()

**Purpose:** Get all programs that don't have streams.

**Returns:**
- QuerySet of Program objects

**Query:**
```python
Program.objects.filter(has_streams=False).order_by('program_name')
```

---

### Method: get_with_streams(program_id)

**Purpose:** Get program with all its streams (eager loading).

**Parameters:**
- `program_id` (int, required)

**Returns:**
- Program object with streams prefetched

**Query:**
```python
Program.objects.prefetch_related('streams').get(program_id=program_id)
```

**Use Case:** When you need program and all its streams

---

### Method: get_with_courses(program_id)

**Purpose:** Get program with all its courses (eager loading).

**Parameters:**
- `program_id` (int, required)

**Returns:**
- Program object with courses prefetched

**Query:**
```python
Program.objects.prefetch_related('courses').get(program_id=program_id)
```

---

### Method: create(data)

**Purpose:** Create new program.

**Parameters:**
- `data` (dict, required):
  ```python
  {
      'program_name': 'Bachelor of Computer Science',
      'program_code': 'BCS',
      'department_name': 'Computer Science',
      'has_streams': True
  }
  ```

**Returns:**
- Created Program object

**Logic:**
```python
program = Program.objects.create(**data)
return program
```

**Note:** Validation happens in model's clean() method

---

### Method: update(program_id, data)

**Purpose:** Update program fields.

**Parameters:**
- `program_id` (int, required)
- `data` (dict, required) - Fields to update

**Returns:**
- Updated Program object

**Logic:**
```python
program = Program.objects.get(program_id=program_id)
for key, value in data.items():
    setattr(program, key, value)
program.save()
return program
```

**Note:** Cannot update program_code (students depend on it)

---

### Method: delete(program_id)

**Purpose:** Hard delete program (cascades to streams and courses).

**Parameters:**
- `program_id` (int, required)

**Returns:**
- None

**Logic:**
```python
program = Program.objects.get(program_id=program_id)
program.delete()
```

**Important:** Check `can_be_deleted()` before calling this

---

### Method: can_be_deleted(program_id)

**Purpose:** Check if program can be safely deleted.

**Parameters:**
- `program_id` (int, required)

**Returns:**
- Boolean (True if safe to delete)

**Logic:**
```python
program = Program.objects.get(program_id=program_id)
has_students = program.students.exists()  # Cross-context check
has_courses = program.courses.exists()
return not (has_students or has_courses)
```

**Use Case:** Validation before deletion

---

## 1.3 ProgramRepository Query Optimization

**Use prefetch_related for:**
- `streams` (reverse ForeignKey)
- `courses` (reverse ForeignKey)
- `students` (reverse ForeignKey, cross-context)

**Example:**
```python
# Avoid N+1 when listing programs with stream counts
programs = Program.objects.prefetch_related('streams').all()
for program in programs:
    print(f"{program.program_name}: {program.streams.count()} streams")
```

---

## 1.4 ProgramRepository Error Handling

**Exceptions:**
- `Program.DoesNotExist` - Program not found
- `IntegrityError` - Duplicate program_code or program_name
- `ValidationError` - Invalid program_code format

**Custom Exceptions (define in service layer):**
- `ProgramNotFoundError`
- `ProgramCodeAlreadyExistsError`
- `ProgramCannotBeDeletedError`

---

# PART 2: STREAM REPOSITORY

## 2.1 StreamRepository Overview

**Purpose:** Handles all data access operations for the Stream model.

**File:** `repositories/stream_repository.py`

**Dependencies:**
- Stream model (from models.py)
- Program model (foreign key)

**Responsibilities:**
- CRUD operations for streams
- Query streams by program
- Query streams by year
- Check stream constraints

---

## 2.2 StreamRepository Methods

### Method: get_by_id(stream_id)

**Purpose:** Retrieve stream by primary key.

**Parameters:**
- `stream_id` (int, required)

**Returns:**
- Stream object

**Raises:**
- `Stream.DoesNotExist` if not found

**Query:**
```python
Stream.objects.get(stream_id=stream_id)
```

---

### Method: find_by_id(stream_id)

**Purpose:** Retrieve stream by primary key, return None if not found.

**Parameters:**
- `stream_id` (int, required)

**Returns:**
- Stream object or None

---

### Method: list_by_program(program_id)

**Purpose:** Get all streams for a specific program.

**Parameters:**
- `program_id` (int, required)

**Returns:**
- QuerySet of Stream objects

**Query:**
```python
Stream.objects.filter(program_id=program_id).order_by('year_of_study', 'stream_name')
```

**Use Case:** Listing streams when creating student profile

---

### Method: list_by_program_and_year(program_id, year_of_study)

**Purpose:** Get streams for specific program and year.

**Parameters:**
- `program_id` (int, required)
- `year_of_study` (int, required) - 1-4

**Returns:**
- QuerySet of Stream objects

**Query:**
```python
Stream.objects.filter(
    program_id=program_id,
    year_of_study=year_of_study
).order_by('stream_name')
```

**Use Case:** When student is in Year 2, show only Year 2 streams

---

### Method: exists_by_program_and_name(program_id, stream_name, year_of_study)

**Purpose:** Check if stream already exists for program/year.

**Parameters:**
- `program_id` (int, required)
- `stream_name` (string, required)
- `year_of_study` (int, required)

**Returns:**
- Boolean

**Query:**
```python
Stream.objects.filter(
    program_id=program_id,
    stream_name=stream_name,
    year_of_study=year_of_study
).exists()
```

**Use Case:** Validation before creating stream (unique_together constraint)

---

### Method: get_with_program(stream_id)

**Purpose:** Get stream with program info (eager loading).

**Parameters:**
- `stream_id` (int, required)

**Returns:**
- Stream object with program loaded

**Query:**
```python
Stream.objects.select_related('program').get(stream_id=stream_id)
```

---

### Method: get_with_students(stream_id)

**Purpose:** Get stream with all students (eager loading, cross-context).

**Parameters:**
- `stream_id` (int, required)

**Returns:**
- Stream object with students prefetched

**Query:**
```python
Stream.objects.prefetch_related('students').get(stream_id=stream_id)
```

**Note:** `students` is reverse relation from StudentProfile (cross-context)

---

### Method: create(data)

**Purpose:** Create new stream.

**Parameters:**
- `data` (dict, required):
  ```python
  {
      'stream_name': 'Stream A',
      'program_id': 5,
      'year_of_study': 2
  }
  ```

**Returns:**
- Created Stream object

**Logic:**
```python
stream = Stream.objects.create(**data)
return stream
```

---

### Method: update(stream_id, data)

**Purpose:** Update stream fields.

**Parameters:**
- `stream_id` (int, required)
- `data` (dict, required)

**Returns:**
- Updated Stream object

---

### Method: delete(stream_id)

**Purpose:** Hard delete stream.

**Parameters:**
- `stream_id` (int, required)

**Returns:**
- None

**Important:** Check `can_be_deleted()` before calling

---

### Method: can_be_deleted(stream_id)

**Purpose:** Check if stream can be safely deleted.

**Parameters:**
- `stream_id` (int, required)

**Returns:**
- Boolean (True if no students assigned)

**Logic:**
```python
stream = Stream.objects.get(stream_id=stream_id)
return not stream.students.exists()  # Cross-context check
```

---

## 2.3 StreamRepository Query Optimization

**Use select_related for:**
- `program` (ForeignKey)

**Use prefetch_related for:**
- `students` (reverse ForeignKey, cross-context)

**Example:**
```python
# Avoid N+1 when listing streams with program names
streams = Stream.objects.select_related('program').filter(year_of_study=2)
for stream in streams:
    print(f"{stream.stream_name} - {stream.program.program_name}")
```

---

## 2.4 StreamRepository Error Handling

**Exceptions:**
- `Stream.DoesNotExist` - Stream not found
- `IntegrityError` - Duplicate stream (unique_together violation)
- `ValidationError` - Invalid year_of_study or program doesn't have streams

**Custom Exceptions:**
- `StreamNotFoundError`
- `StreamAlreadyExistsError`
- `StreamCannotBeDeletedError`

---

# PART 3: COURSE REPOSITORY

## 3.1 CourseRepository Overview

**Purpose:** Handles all data access operations for the Course model.

**File:** `repositories/course_repository.py`

**Dependencies:**
- Course model (from models.py)
- Program model (foreign key)
- LecturerProfile model (foreign key, cross-context)

**Responsibilities:**
- CRUD operations for courses
- Query courses by program
- Query courses by lecturer
- Check course constraints
- Handle nullable lecturer field

---

## 3.2 CourseRepository Methods

### Method: get_by_id(course_id)

**Purpose:** Retrieve course by primary key.

**Parameters:**
- `course_id` (int, required)

**Returns:**
- Course object

**Raises:**
- `Course.DoesNotExist` if not found

**Query:**
```python
Course.objects.get(course_id=course_id)
```

---

### Method: find_by_id(course_id)

**Purpose:** Retrieve course by primary key, return None if not found.

**Parameters:**
- `course_id` (int, required)

**Returns:**
- Course object or None

---

### Method: get_by_code(course_code)

**Purpose:** Retrieve course by course code (e.g., "CS201").

**Parameters:**
- `course_code` (string, required)

**Returns:**
- Course object

**Raises:**
- `Course.DoesNotExist` if not found

**Query:**
```python
Course.objects.get(course_code=course_code.upper())
```

---

### Method: exists_by_code(course_code)

**Purpose:** Check if course code already exists.

**Parameters:**
- `course_code` (string, required)

**Returns:**
- Boolean

**Query:**
```python
Course.objects.filter(course_code=course_code.upper()).exists()
```

---

### Method: list_by_program(program_id)

**Purpose:** Get all courses for a specific program.

**Parameters:**
- `program_id` (int, required)

**Returns:**
- QuerySet of Course objects

**Query:**
```python
Course.objects.filter(program_id=program_id).order_by('course_code')
```

---

### Method: list_by_lecturer(lecturer_id)

**Purpose:** Get all courses assigned to a lecturer.

**Parameters:**
- `lecturer_id` (int, required)

**Returns:**
- QuerySet of Course objects

**Query:**
```python
Course.objects.filter(lecturer_id=lecturer_id).order_by('course_code')
```

**Use Case:** Listing courses taught by a lecturer

---

### Method: list_unassigned()

**Purpose:** Get all courses with no assigned lecturer.

**Returns:**
- QuerySet of Course objects

**Query:**
```python
Course.objects.filter(lecturer__isnull=True).order_by('course_code')
```

**Use Case:** Admin needs to assign lecturers

---

### Method: get_with_program(course_id)

**Purpose:** Get course with program info (eager loading).

**Parameters:**
- `course_id` (int, required)

**Returns:**
- Course object with program loaded

**Query:**
```python
Course.objects.select_related('program').get(course_id=course_id)
```

---

### Method: get_with_lecturer(course_id)

**Purpose:** Get course with lecturer info (eager loading, cross-context).

**Parameters:**
- `course_id` (int, required)

**Returns:**
- Course object with lecturer and user loaded

**Query:**
```python
Course.objects.select_related('lecturer__user').get(course_id=course_id)
```

**Note:** Uses double underscore to traverse lecturer → user relationship

---

### Method: get_full_info(course_id)

**Purpose:** Get course with all related data (program, lecturer).

**Parameters:**
- `course_id` (int, required)

**Returns:**
- Course object with all relations loaded

**Query:**
```python
Course.objects.select_related('program', 'lecturer__user').get(course_id=course_id)
```

---

### Method: create(data)

**Purpose:** Create new course.

**Parameters:**
- `data` (dict, required):
  ```python
  {
      'course_name': 'Data Structures and Algorithms',
      'course_code': 'CS201',
      'program_id': 5,
      'department_name': 'Computer Science',
      'lecturer_id': None  # Optional, can be NULL
  }
  ```

**Returns:**
- Created Course object

**Logic:**
```python
course = Course.objects.create(**data)
return course
```

---

### Method: update(course_id, data)

**Purpose:** Update course fields.

**Parameters:**
- `course_id` (int, required)
- `data` (dict, required)

**Returns:**
- Updated Course object

---

### Method: assign_lecturer(course_id, lecturer_id)

**Purpose:** Assign lecturer to course.

**Parameters:**
- `course_id` (int, required)
- `lecturer_id` (int, required)

**Returns:**
- Updated Course object

**Logic:**
```python
course = Course.objects.get(course_id=course_id)
course.lecturer_id = lecturer_id
course.save()
return course
```

**Use Case:** Admin assigning lecturer to course

---

### Method: unassign_lecturer(course_id)

**Purpose:** Remove lecturer from course (set to NULL).

**Parameters:**
- `course_id` (int, required)

**Returns:**
- Updated Course object

**Logic:**
```python
course = Course.objects.get(course_id=course_id)
course.lecturer_id = None
course.save()
return course
```

---

### Method: delete(course_id)

**Purpose:** Hard delete course.

**Parameters:**
- `course_id` (int, required)

**Returns:**
- None

**Important:** Check `can_be_deleted()` before calling

---

### Method: can_be_deleted(course_id)

**Purpose:** Check if course can be safely deleted.

**Parameters:**
- `course_id` (int, required)

**Returns:**
- Boolean (True if no sessions exist)

**Logic:**
```python
course = Course.objects.get(course_id=course_id)
return not course.sessions.exists()  # Cross-context check
```

**Note:** `sessions` is reverse relation from Session model (cross-context)

---

## 3.3 CourseRepository Query Optimization

**Use select_related for:**
- `program` (ForeignKey)
- `lecturer` (ForeignKey, nullable)
- `lecturer__user` (nested relation to get lecturer name)

**Use prefetch_related for:**
- `sessions` (reverse ForeignKey, cross-context)

**Example:**
```python
# Avoid N+1 when listing courses with program and lecturer names
courses = Course.objects.select_related('program', 'lecturer__user').all()
for course in courses:
    program_name = course.program.program_name
    lecturer_name = course.get_lecturer_name()  # Uses model method
    print(f"{course.course_code}: {program_name} - {lecturer_name}")
```

---

## 3.4 CourseRepository Nullable Field Handling

**lecturer Field (NULLABLE):**
- Can be NULL when course is first created
- Must be set before lecturer can create sessions
- Filter for NULL: `Course.objects.filter(lecturer__isnull=True)`
- Filter for NOT NULL: `Course.objects.filter(lecturer__isnull=False)`

**Example Queries:**
```python
# Get assigned courses
assigned_courses = Course.objects.filter(lecturer__isnull=False)

# Get unassigned courses
unassigned_courses = Course.objects.filter(lecturer__isnull=True)

# Check if course has lecturer
course = Course.objects.get(course_id=5)
if course.lecturer:
    print(f"Taught by {course.lecturer.user.get_full_name()}")
else:
    print("No lecturer assigned")
```

---

## 3.5 CourseRepository Error Handling

**Exceptions:**
- `Course.DoesNotExist` - Course not found
- `IntegrityError` - Duplicate course_code
- `ValidationError` - Invalid course_code format or inactive lecturer

**Custom Exceptions:**
- `CourseNotFoundError`
- `CourseCodeAlreadyExistsError`
- `CourseCannotBeDeletedError`
- `LecturerNotFoundError` (when assigning)

---

# PART 4: CROSS-CONTEXT INTEGRATION

## 4.1 Integration with User Management Context

**Validating Lecturer:**
```python
# Check if lecturer exists and is active
from user_management.repositories import LecturerProfileRepository

lecturer_repo = LecturerProfileRepository()
lecturer = lecturer_repo.get_by_id(lecturer_id)
if not lecturer.user.is_active:
    raise ValidationError("Cannot assign inactive lecturer")
```

**Accessing Lecturer Info:**
```python
# Get course with lecturer name
course = Course.objects.select_related('lecturer__user').get(course_id=5)
lecturer_name = course.lecturer.user.get_full_name() if course.lecturer else "Not Assigned"
```

---

## 4.2 Integration with Session Management Context

**Checking if Course Can Be Deleted:**
```python
# Check if course has sessions (cross-context)
course = Course.objects.get(course_id=5)
has_sessions = course.sessions.exists()  # Assumes 'sessions' reverse relation
if has_sessions:
    raise ValidationError("Cannot delete course with existing sessions")
```

---

## 4.3 Integration Pattern

**Repository should NOT directly access other context's repositories.**
**Service layer handles cross-context validation.**

**Example (in service layer, not repository):**
```python
# Service method
def assign_lecturer_to_course(course_id, lecturer_id):
    # 1. Validate lecturer exists (call User Management service)
    lecturer = user_service.get_lecturer_by_id(lecturer_id)
    if not lecturer.user.is_active:
        raise InactiveLecturerError()
    
    # 2. Assign in repository
    course = course_repository.assign_lecturer(course_id, lecturer_id)
    
    return course
```

---

# PART 5: COMMON PATTERNS

## 5.1 Query Patterns

**Pattern 1: List with Related Data**
```python
# Get all courses with program and lecturer
courses = Course.objects.select_related('program', 'lecturer__user').all()
```

**Pattern 2: Check Existence Before Create**
```python
# Validate program code doesn't exist
if program_repository.exists_by_code(program_code):
    raise ProgramCodeAlreadyExistsError()
```

**Pattern 3: Safe Delete**
```python
# Check before delete
if not program_repository.can_be_deleted(program_id):
    raise ProgramCannotBeDeletedError("Program has students or courses")
program_repository.delete(program_id)
```

**Pattern 4: Filtering by Nullable Field**
```python
# Get unassigned courses
unassigned = course_repository.list_unassigned()  # WHERE lecturer_id IS NULL
```

---

## 5.2 Return Type Specifications

**get_* methods:**
- Return single object
- Raise DoesNotExist if not found

**find_* methods:**
- Return single object or None
- Never raise exception

**list_* methods:**
- Return QuerySet (can be empty)
- Never return None

**exists_* methods:**
- Return boolean
- Never raise exception

**create/update/delete methods:**
- Return object (create/update) or None (delete)
- Raise DoesNotExist if ID not found

---

## 5.3 Method Naming Conventions

- `get_by_*` - Single object, raises exception
- `find_by_*` - Single object, returns None
- `list_*` - Multiple objects, returns QuerySet
- `exists_*` - Boolean check
- `create` - Create new record
- `update` - Update existing record
- `delete` - Delete record
- `can_be_deleted` - Check if safe to delete

---

**Status**: 📋 Complete repository specification ready for implementation