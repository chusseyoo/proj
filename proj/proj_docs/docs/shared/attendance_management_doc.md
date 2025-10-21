# 📘 Documentation: Attendance Management Bounded Context

## 1. Purpose & Scope

The **Attendance Management bounded context** handles all attendance tracking functionality within the QR-based attendance system.

- Provides session creation, QR code scanning, and attendance recording.
- Issues and verifies short-lived JWT tokens for attendance links.
- Validates student location against lecturer location (30-meter radius).
- Manages programs, streams, courses, and student enrollment.
- No roles beyond Admin, Lecturer, and Student.

---

## 2. Constraints & Guiding Principles

- **KISS (Keep It Simple, Stupid):** only implement essential features (session creation, attendance marking, basic reporting).
- **Separation of Concerns:**
  - Presentation (API endpoints)
  - Application (use cases/handlers)
  - Domain (entities, value objects, services, repositories)
  - Infrastructure (DB, JWT, email, location services)
- **Modular Monolith:** internal communication between bounded contexts (direct calls).
- **Time Constraint:** 1-week MVP, 4-person team → only core features.
- **Security Constraint:**
  - Passwords always hashed (bcrypt).
  - Short-lived JWT tokens for attendance (30 minutes).
  - Location validation enforced server-side.

---

## 3. Functional Requirements

- Register lecturers (self-registration with admin activation).
- Create attendance sessions for specific courses and programs/streams.
- Generate short-lived attendance links with JWT tokens.
- Send automated email notifications to students.
- Allow students to mark attendance via QR code scan + location.
- Validate student location within 30 meters of lecturer.
- Prevent duplicate attendance for same session.
- Generate attendance reports by session.

---

## 4. User Stories

### Lecturer Registration
- **As a** new lecturer
- **I want** to self-register with my email, password, name, employee ID, and department
- **So that** I can create attendance sessions after admin activation

**Acceptance Criteria:**
- Unique email
- Password stored securely (hashed)
- Admin can activate/deactivate accounts
- Password field is NOT nullable for lecturers

### Create Session
- **As a** lecturer
- **I want** to create an attendance session for my course
- **So that** students can mark their attendance

**Acceptance Criteria:**
- Session linked to specific course and program/stream
- Lecturer's location captured
- Short-lived JWT token generated
- Email notifications sent automatically

### Mark Attendance
- **As a** student
- **I want** to scan my QR code and submit my location
- **So that** my attendance is recorded

**Acceptance Criteria:**
- Valid attendance token required
- Student within 30 meters of lecturer
- No duplicate attendance allowed
- Timestamp and location stored

### View Attendance Report
- **As a** lecturer or admin
- **I want** to view attendance reports for a session
- **So that** I can track student participation

**Acceptance Criteria:**
- List all students in target program/stream
- Show attendance status for each student
- Export to CSV/Excel

---

## 5. User Flows

### 5.1 Lecturer Registration Flow
```
Lecturer → API /auth/register → RegisterLecturerHandler → UserService.registerLecturer()
  → Password.hash → UserRepository.save() → Admin activates → Success response
```

### 5.2 Create Session Flow
```
Lecturer → API /sessions (POST) → CreateSessionHandler → SessionService.createSession()
  → SessionRepository.save() → Identify eligible students (by program/stream)
  → For each student: JWTProvider.createAttendanceToken() 
  → EmailNotificationRepository.save() → EmailService.queueEmails()
  → Background worker sends emails → Success response
```

### 5.3 Mark Attendance Flow
```
Student → Email link with token → Opens attendance page → Scans QR code
  → API /attendance/mark → MarkAttendanceHandler
  → JWTProvider.verifyToken() → Extract student_id from QR code
  → Validate student eligibility (program/stream match)
  → LocationValidator.validateDistance(student_location, session_location, 30m)
  → Check duplicate attendance (UNIQUE constraint)
  → AttendanceRepository.save() → Success response
```

### 5.4 View Report Flow
```
Lecturer → API /sessions/{id}/report → GenerateReportHandler
  → AttendanceRepository.findBySession() → ReportService.generate()
  → Success response with report data
```

---

## 6. Domain Model (UML Overview)

```plaintext
+-------------------+
|      User         |
+-------------------+
| - user_id: Integer |
| - email: String   |
| - password: String (nullable) |
| - first_name: String |
| - last_name: String |
| - role: Enum      |
| - is_active: Boolean |
| - date_joined: DateTime |
+-------------------+
| + authenticate(password: String): Boolean |
| + activate() |
| + deactivate() |
+-------------------+

+-------------------+
|  LecturerProfile  |
+-------------------+
| - lecturer_id: Integer |
| - user_id: Integer |
| - department_name: String |
+-------------------+

+-------------------+
|  StudentProfile   |
+-------------------+
| - student_id: Integer |
| - user_id: Integer |
| - program_id: Integer |
| - stream_id: Integer (nullable) |
| - year_of_study: Integer |
| - qr_code_data: String |
+-------------------+

+-------------------+
|     Session       |
+-------------------+
| - session_id: Integer |
| - course_id: Integer |
| - lecturer_id: Integer |
| - program_id: Integer |
| - stream_id: Integer (nullable) |
| - date_created: Date |
| - time_created: DateTime |
| - time_ended: DateTime |
| - latitude: Decimal |
| - longitude: Decimal |
+-------------------+
| + isActive(): Boolean |
| + hasExpired(): Boolean |
+-------------------+

+-------------------+
|    Attendance     |
+-------------------+
| - attendance_id: Integer |
| - session_id: Integer |
| - student_id: Integer |
| - time_recorded: DateTime |
| - latitude: Decimal |
| - longitude: Decimal |
| - status: String |
| - is_within_radius: Boolean |
+-------------------+

+-------------------+
| EmailNotification |
+-------------------+
| - email_id: Integer |
| - session_id: Integer |
| - student_id: Integer |
| - token: String |
| - token_expires_at: DateTime |
| - status: Enum |
| - created_at: DateTime |
| - sent_at: DateTime (nullable) |
+-------------------+

+-------------------+
| LocationValidator |
+-------------------+
| + validateDistance(lat1, lon1, lat2, lon2, maxMeters): Boolean |
| + calculateHaversineDistance(lat1, lon1, lat2, lon2): Float |
+-------------------+

+-------------------+
|   JWTProvider     |
+-------------------+
| + createAttendanceToken(sessionId, expiryMinutes): String |
| + verifyToken(token): TokenClaims |
+-------------------+
```

---

## 7. Database Schema

```sql
CREATE TABLE users (
  user_id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255),  -- Nullable for students
  first_name VARCHAR(255) NOT NULL,
  last_name VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL,
  is_active BOOLEAN DEFAULT FALSE,
  date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lecturer_profiles (
  lecturer_id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(user_id),
  department_name VARCHAR(255) NOT NULL
);

CREATE TABLE student_profiles (
  student_id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(user_id),
  program_id INTEGER NOT NULL REFERENCES programs(program_id),
  stream_id INTEGER REFERENCES streams(stream_id),
  year_of_study INTEGER NOT NULL,
  qr_code_data VARCHAR(255) NOT NULL
);

CREATE TABLE programs (
  program_id SERIAL PRIMARY KEY,
  program_name VARCHAR(255) NOT NULL,
  program_code VARCHAR(50) NOT NULL,
  department_name VARCHAR(255) NOT NULL,
  has_streams BOOLEAN DEFAULT FALSE
);

CREATE TABLE streams (
  stream_id SERIAL PRIMARY KEY,
  program_id INTEGER NOT NULL REFERENCES programs(program_id),
  stream_name VARCHAR(255) NOT NULL,
  year_of_study INTEGER NOT NULL
);

CREATE TABLE courses (
  course_id SERIAL PRIMARY KEY,
  program_id INTEGER NOT NULL REFERENCES programs(program_id),
  course_code VARCHAR(50) NOT NULL,
  course_name VARCHAR(255) NOT NULL,
  department_name VARCHAR(255) NOT NULL,
  lecturer_id INTEGER REFERENCES lecturer_profiles(lecturer_id)
);

CREATE TABLE sessions (
  session_id SERIAL PRIMARY KEY,
  course_id INTEGER NOT NULL REFERENCES courses(course_id),
  lecturer_id INTEGER NOT NULL REFERENCES lecturer_profiles(lecturer_id),
  program_id INTEGER NOT NULL REFERENCES programs(program_id),
  stream_id INTEGER REFERENCES streams(stream_id),
  date_created DATE NOT NULL,
  time_created TIMESTAMP NOT NULL,
  time_ended TIMESTAMP NOT NULL,
  latitude DECIMAL(10, 8) NOT NULL,
  longitude DECIMAL(11, 8) NOT NULL
);

CREATE TABLE attendance (
  attendance_id SERIAL PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(session_id),
  student_id INTEGER NOT NULL REFERENCES student_profiles(student_id),
  time_recorded TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  latitude DECIMAL(10, 8) NOT NULL,
  longitude DECIMAL(11, 8) NOT NULL,
  status VARCHAR(50) NOT NULL,
  is_within_radius BOOLEAN NOT NULL,
  UNIQUE(session_id, student_id)
);

CREATE TABLE reports (
  report_id SERIAL PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(session_id),
  generated_by INTEGER NOT NULL REFERENCES users(user_id),
  generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  file_path VARCHAR(500),
  file_type VARCHAR(50)
);

CREATE TABLE email_notifications (
  email_id SERIAL PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(session_id),
  student_id INTEGER NOT NULL REFERENCES student_profiles(student_id),
  token VARCHAR(500) NOT NULL,
  token_expires_at TIMESTAMP NOT NULL,
  status VARCHAR(50) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  sent_at TIMESTAMP,
  UNIQUE(session_id, student_id)
);
```

---

## 8. API Endpoints

### Authentication
- `POST /api/v1/auth/register` → register lecturer (requires admin activation)
- `POST /api/v1/auth/login` → login, returns JWT

### Sessions
- `POST /api/v1/sessions/` → create session (requires lecturer JWT)
- `GET /api/v1/sessions/` → list sessions (requires JWT)
- `GET /api/v1/sessions/{id}/` → get session details
- `POST /api/v1/sessions/{id}/validate-token/` → validate attendance token

### Attendance
- `POST /api/v1/attendance/mark/` → mark attendance (requires JWT token from email + QR scan)

### Reports
- `GET /api/v1/sessions/{id}/report/` → generate attendance report

---

## 9. Responsibilities & Module Boundaries

- **Domain layer:** `User`, `Session`, `Attendance`, `Program`, `Stream`, `Course`, value objects, services
- **Application layer:** Handlers for each use case (RegisterLecturerHandler, CreateSessionHandler, MarkAttendanceHandler, etc.)
- **Infrastructure layer:**
  - `UserRepositoryImpl` (SQL/ORM)
  - `SessionRepositoryImpl` (SQL/ORM)
  - `AttendanceRepositoryImpl` (SQL/ORM)
  - `EmailNotificationRepositoryImpl` (SQL/ORM)
  - `ProgramRepositoryImpl` (SQL/ORM)
  - `CourseRepositoryImpl` (SQL/ORM)
  - `JWTProvider` (token generation/verification)
  - `EmailService` (SMTP/background queue worker)
  - `LocationValidator` (Haversine distance calculation for 30m radius)
- **Presentation layer:** REST controllers mapping HTTP → application handlers
