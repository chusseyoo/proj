# models_guide.md

Brief: Specification for the Session model in Session Management. Defines fields, relationships, constraints, and validations. Sessions cannot exist without a lecturer.

---

## Model Overview
- Session: lecturer-created session for a specific course, targeting a program (and optionally a stream), with a time window and captured GPS location.

---

# SESSION

Purpose
- Enable a lecturer to open a time-bounded session for students to act against (e.g., attendance), with origin location recorded.

Fields (NOT NULL unless noted)
- session_id: Auto-increment PK
- program: FK → Program (Academic Structure), on_delete=CASCADE
- course: FK → Course (Academic Structure), on_delete=CASCADE
- lecturer: FK → LecturerProfile (User Management), on_delete=PROTECT
  - Rationale: Session requires a lecturer; prevent deleting lecturer with sessions
- stream: FK → Stream (Academic Structure), NULLABLE, on_delete=SET_NULL
  - Null targets entire program; non-null targets specific stream in the same program

Time Window
- time_created: DateTime (TZ), start of session window
- time_ended: DateTime (TZ), end of session window

Location (captured at creation)
- latitude: Decimal(10,8), range [-90, 90]
- longitude: Decimal(11,8), range [-180, 180]
- location_description: String (<=100), NULLABLE

Constraints and Indexes
- CHECK: time_ended > time_created
- CHECK: latitude/longitude within valid ranges
- Indexes:
  - (course_id)
  - (lecturer_id)
  - (program_id, stream_id)
  - (time_created, time_ended)

Derived Status (not stored)
- created: record exists
- active: now in [time_created, time_ended)
- ended: now ≥ time_ended

Validations (Service-enforced)
- Lecturer must be active and assigned to the course
- Program and course must exist; course must belong to program
- If program.has_streams=False ⇒ stream must be NULL
- If stream provided ⇒ it must belong to the program
- No overlapping sessions for the same lecturer
- Duration bounds recommended: 10 minutes to 24 hours

Example (conceptual)
- program: BCS (id=1), course: CS201 (id=301), lecturer: 17
- stream: NULL, time_created: 2025-10-25T08:00:00Z, time_ended: 2025-10-25T10:00:00Z
- latitude: -1.28333412, longitude: 36.81666588, location_description: "Room A101"