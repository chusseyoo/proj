# README.md

Brief: Overview and implementation manual for Academic Structure context. Describes scope, entities, business rules, and integration points.

# Academic Structure Bounded Context

## Purpose

This bounded context manages the academic organizational structure including programs, streams, and courses. It defines how students are grouped and how courses are organized within the institution.

## Scope

### What This Context Handles
- Program management (degree programs)
- Stream management (subdivisions within programs)
- Course management (individual courses taught in programs)
- Program-Stream relationships
- Program-Course relationships
- Lecturer-Course assignments

### What This Context Does NOT Handle
- User management (students, lecturers) → handled by User Management Context
- Session creation → handled by Session Management Context
- Attendance tracking → handled by Attendance Recording Context
- Email notifications → handled by Email Notification Context
- Reporting → handled by Reporting Context

## Core Entities

### Program
- **Primary entity** representing academic programs (e.g., Bachelor of Computer Science)
- Attributes:
  - `program_id` (Primary Key, Integer, Auto-increment) - Unique identifier
  - `program_name` (String, NOT NULL) - Full name of the program
    - Example: "Bachelor of Computer Science", "Bachelor of Engineering"
  - `program_code` (String, NOT NULL, UNIQUE) - 3-letter abbreviation
    - Pattern: 3 uppercase letters
    - Example: "BCS", "ENG", "MED"
    - Regex: `^[A-Z]{3}$`
    - **Used as prefix in student IDs** (e.g., `BCS/234344`)
  - `department_name` (String, NOT NULL) - Department offering the program
  - `has_streams` (Boolean, NOT NULL, Default: False) - Whether program has stream subdivisions

**Important Notes:**
- `program_code` must be unique and match student ID prefix
- If `has_streams = True`, the program MUST have at least one Stream
- If `has_streams = False`, the program should NOT have any Streams
- Students enrolled in this program will have `program_id` foreign key
- Courses in this program will have `program_id` foreign key

### Stream
- **Subdivision entity** within programs (e.g., Stream A, Stream B)
- Attributes:
  - `stream_id` (Primary Key, Integer, Auto-increment) - Unique identifier
  - `stream_name` (String, NOT NULL) - Name of the stream
    - Example: "Stream A", "Stream B", "Morning Stream", "Evening Stream"
  - `program_id` (Foreign Key → Program.program_id, NOT NULL) - Parent program
  - `year_of_study` (Integer, NOT NULL) - Which year this stream is for (1-4)

**Important Notes:**
- Only exists if parent Program has `has_streams = True`
- Multiple streams can exist for the same program and year
- CASCADE DELETE: Deleting a Program deletes all its Streams
- Students in streamed programs must have a `stream_id`
- Sessions can target specific streams OR entire programs

### Course
- **Course entity** representing individual courses taught in programs
- Attributes:
  - `course_id` (Primary Key, Integer, Auto-increment) - Unique identifier
  - `course_name` (String, NOT NULL) - Full name of the course
    - Example: "Data Structures and Algorithms", "Database Systems"
  - `course_code` (String, NOT NULL, UNIQUE) - Short code for the course
    - Example: "CS201", "ENG301", "MED405"
  - `program_id` (Foreign Key → Program.program_id, NOT NULL) - Program offering this course
  - `department_name` (String, NOT NULL) - Department teaching the course
  - `lecturer_id` (Foreign Key → LecturerProfile.lecturer_id, **NULLABLE**) - Assigned lecturer
    - **NULL if no lecturer assigned yet**
    - **NOT NULL when course is active and being taught**

**Important Notes:**
- Each course belongs to exactly one program
- `course_code` must be unique across entire system
- `lecturer_id` is nullable initially, must be set before creating sessions
- CASCADE: Deleting a Program deletes all its Courses
- SET NULL: Deleting a Lecturer sets `lecturer_id` to NULL (course remains)
- Only the assigned lecturer can create sessions for this course

## Business Rules

### Program Management

1. **Creating Programs**:
   - Admin only
   - `program_code` must be unique 3-letter code
   - `has_streams` determines if streams are required
   - Cannot be deleted if students are enrolled or courses exist

2. **Program with Streams**:
   - If `has_streams = True`, must create at least one Stream
   - Students in this program MUST be assigned to a stream
   - Sessions can target entire program OR specific streams

3. **Program without Streams**:
   - If `has_streams = False`, no Streams should exist
   - All students in program have `stream_id = NULL`
   - Sessions always target entire program

### Stream Management

1. **Creating Streams**:
   - Admin only
   - Can only create streams for programs with `has_streams = True`
   - Must specify `year_of_study` (1-4)
   - Multiple streams can exist for same year (e.g., Stream A and Stream B for Year 1)

2. **Stream Assignment**:
   - Students in streamed programs must be assigned to a stream
   - Stream must belong to student's program
   - Cannot delete stream if students are assigned to it

### Course Management

1. **Creating Courses**:
   - Admin only
   - Must belong to a program
   - `course_code` must be unique
   - `lecturer_id` is optional initially

2. **Lecturer Assignment**:
   - Admin can assign/reassign lecturers to courses
   - One lecturer per course (no team teaching)
   - Lecturer must have active account
   - Changing lecturer does NOT affect existing sessions

3. **Course Deletion**:
   - Can only delete if no sessions exist
   - Warns if sessions exist for the course

## Validation Rules

### Program Code Validation
- Must be exactly 3 uppercase letters
- Regex: `^[A-Z]{3}$`
- Must be unique across all programs
- Cannot be changed after creation (students IDs depend on it)

### Program Name Validation
- Minimum 5 characters
- Maximum 200 characters
- Must be unique

### Stream Name Validation
- Minimum 2 characters
- Maximum 100 characters
- Should be descriptive (e.g., "Stream A", "Morning Batch")

### Course Code Validation
- Pattern: 2-4 uppercase letters + 3 digits
- Regex: `^[A-Z]{2,4}[0-9]{3}$`
- Example: "CS201", "ENG301", "MATH101"
- Must be unique across all courses

### Course Name Validation
- Minimum 3 characters
- Maximum 200 characters

### Year of Study Validation
- Must be integer between 1 and 4
- Represents academic year level

## Database Constraints

### Program Table
```sql
CREATE TABLE programs (
  program_id SERIAL PRIMARY KEY,
  program_name VARCHAR(200) NOT NULL UNIQUE,
  program_code VARCHAR(3) NOT NULL UNIQUE,
  department_name VARCHAR(100) NOT NULL,
  has_streams BOOLEAN NOT NULL DEFAULT FALSE,
  
  CONSTRAINT valid_program_code_format CHECK (program_code ~ '^[A-Z]{3}$')
);

CREATE UNIQUE INDEX idx_programs_program_code ON programs(program_code);
CREATE INDEX idx_programs_department ON programs(department_name);
```

### Stream Table
```sql
CREATE TABLE streams (
  stream_id SERIAL PRIMARY KEY,
  stream_name VARCHAR(100) NOT NULL,
  program_id INTEGER NOT NULL REFERENCES programs(program_id) ON DELETE CASCADE,
  year_of_study INTEGER NOT NULL CHECK (year_of_study BETWEEN 1 AND 4),
  
  CONSTRAINT unique_stream_per_program UNIQUE(program_id, stream_name, year_of_study)
);

CREATE INDEX idx_streams_program_id ON streams(program_id);
CREATE INDEX idx_streams_year ON streams(year_of_study);
```

### Course Table
```sql
CREATE TABLE courses (
  course_id SERIAL PRIMARY KEY,
  course_name VARCHAR(200) NOT NULL,
  course_code VARCHAR(10) NOT NULL UNIQUE,
  program_id INTEGER NOT NULL REFERENCES programs(program_id) ON DELETE CASCADE,
  department_name VARCHAR(100) NOT NULL,
  lecturer_id INTEGER REFERENCES lecturer_profiles(lecturer_id) ON DELETE SET NULL,  -- NULLABLE
  
  CONSTRAINT valid_course_code_format CHECK (course_code ~ '^[A-Z]{2,4}[0-9]{3}$')
);

CREATE UNIQUE INDEX idx_courses_course_code ON courses(course_code);
CREATE INDEX idx_courses_program_id ON courses(program_id);
CREATE INDEX idx_courses_lecturer_id ON courses(lecturer_id);
```

**Important Constraint Notes:**
- `ON DELETE CASCADE` (Program → Stream, Program → Course): Deleting program removes streams and courses
- `ON DELETE SET NULL` (Lecturer → Course): Deleting lecturer keeps course but removes assignment
- `UNIQUE` on `program_code` and `course_code`: No duplicates
- `CHECK` constraints enforce format patterns
- Unique constraint on stream prevents duplicate stream names per program/year

## Django Implementation Structure

This context will be implemented as a Django app:

```
academic_structure/
├── models.py           # Program, Stream, Course models
├── repositories.py     # ProgramRepository, StreamRepository, CourseRepository
├── services.py         # AcademicStructureService, validation logic
├── handlers.py         # CreateProgramHandler, AssignLecturerHandler, etc.
├── views.py           # API endpoints (admin only)
├── serializers.py     # Request/response serialization
├── validators.py      # Format validation (program_code, course_code)
├── permissions.py     # AdminOnly permission class
├── urls.py            # URL routing
├── tests/             # Unit and integration tests
└── migrations/        # Database migrations
```

## Integration Points

### Outbound Dependencies (What We Call)
- **Infrastructure**: 
  - Database (PostgreSQL)
  
- **User Management Context**: 
  - Validate `lecturer_id` exists when assigning to course
  - Check lecturer is active

### Inbound Dependencies (Who Calls Us)
- **User Management Context**: 
  - Validate `program_id` when creating StudentProfile
  - Validate `stream_id` when creating StudentProfile
  - Check if program `has_streams` to determine stream requirement
  
- **Session Management Context**: 
  - Get program and stream info when creating sessions
  - Validate course belongs to program
  - Get lecturer from course
  
- **Attendance Recording Context**: 
  - Validate student eligibility (program/stream match)
  
- **Reporting Context**: 
  - Get program/course names for reports

## Files in This Context

### 1. `README.md` (this file)
Overview of the bounded context

### 2. `models_guide.md`
Step-by-step guide for creating Django models:
- Program model (with has_streams flag)
- Stream model (nullable relationship)
- Course model (with nullable lecturer_id)
- Model relationships and constraints
- Validation methods

### 3. `repositories_guide.md`
Guide for creating repository layer:
- ProgramRepository (CRUD + check has_streams)
- StreamRepository (query by program, by year)
- CourseRepository (query by program, by lecturer)
- Complex queries

### 4. `services_guide.md`
Guide for creating domain services:
- AcademicStructureService (business logic)
- Validation: program code format, course code format
- Check if program can be deleted
- Stream requirement logic

### 5. `handlers_guide.md`
Guide for creating application layer handlers:
- CreateProgramHandler
- CreateStreamHandler (validate parent program)
- CreateCourseHandler
- AssignLecturerToCourseHandler
- DeleteProgramHandler (check dependencies)

### 6. `views_guide.md`
Guide for creating API endpoints:
- POST /api/v1/admin/programs/
- GET /api/v1/programs/
- POST /api/v1/admin/streams/
- POST /api/v1/admin/courses/
- PATCH /api/v1/admin/courses/{id}/assign-lecturer/
- Admin-only access

### 7. `permissions_guide.md`
Guide for implementing access control:
- AdminOnly permission
- Read-only access for lecturers (view programs/courses)

### 8. `testing_guide.md`
Guide for writing tests:
- Test program with/without streams
- Test stream creation validation
- Test course-lecturer assignment
- Test cascade deletes

## Implementation Order

1. **Models** (`models_guide.md`) - Program, Stream, Course
2. **Repositories** (`repositories_guide.md`) - Data access
3. **Services** (`services_guide.md`) - Business logic and validation
4. **Handlers** (`handlers_guide.md`) - Application orchestration
5. **Serializers & Validators** (part of `views_guide.md`)
6. **Views** (`views_guide.md`) - Admin API endpoints
7. **Permissions** (`permissions_guide.md`) - Admin-only access
8. **Tests** (`testing_guide.md`) - Comprehensive testing

## Next Steps

After reading this overview:
1. Understand program/stream relationship (has_streams flag)
2. Verify nullable lecturer_id in courses
3. Confirm cascade delete behavior
4. Check integration with User Management (program_id, stream_id validation)
5. Proceed to detailed guide files

---

**Status**: 📝 Overview Complete - Ready for detailed guide creation
