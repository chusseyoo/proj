# General Workflow

## System Workflow Overview

The attendance management system follows a four-phase workflow from user registration to report generation.

---

## Phase 1: Registration Phase

### Admin Registers Students
The admin enters student information into the system:
- **Student ID** (format: `BCS/234344` where BCS is program code and 234344 is student number)
- Student first name
- Student last name
- Email address
- Program (selected from dropdown - must match the code in student ID)
- Stream (if applicable)
- Year of study

**System Behavior:**
- Admin enters the institutional student ID (e.g., `BCS/234344`)
- System validates format: 3 uppercase letters + `/` + 6 digits
- System auto-generates:
  - `student_profile_id` - internal database identifier (auto-increment)
  - `user_id` - links to user account (auto-increment)
  - `qr_code_data` - set to match `student_id` (e.g., `BCS/234344`)

**QR Code Note:** 
- Physical QR codes on student ID cards must contain their student ID in the format: `BCS/234344`
- The system does NOT generate QR codes - they are printed externally
- QR code content must exactly match the registered student_id

### Lecturer Self-Registration / Activation
- Lecturers register themselves (self-service) or request an account:
  - First name
  - Last name
  - Email address
  - Employee ID
  - Password
  - Department name
- Admins may activate or manage lecturer accounts but CANNOT create new lecturer accounts directly.
**Note:** Students do NOT self-register or create accounts. All student data is entered by administrators.

---

## Phase 2: Session Creation Phase

### Lecturer Actions
1. Lecturer logs into the system
2. Lecturer creates an attendance session for a specific course
3. Lecturer selects target audience:
   - Entire program, OR
   - Specific stream within a program
4. System captures lecturer's current GPS location

### System Actions
1. System identifies all students in the target program/stream
2. System automatically generates email notifications
3. System sends emails to all eligible students with:
   - Session details
   - Direct link to attendance page
   - Session time information

---

## Phase 3: Attendance Recording Phase

### Student Actions
1. Student receives email notification
2. Student opens the attendance page link
3. Student scans their QR code (generated externally, from their physical ID card)
   - **QR code contains:** `BCS/234344` (their registered student ID)
   - **System extracts:** Student ID from QR code
   - **System validates:** Scanned ID matches the student associated with the email link

### System Validation
1. Decode token → get `student_profile_id` and `session_id`
2. Load StudentProfile → compare `student_id` with scanned QR value
3. Validate eligibility (program/stream)
4. Validate session active and within time window
5. Validate GPS within 30 meters
6. Prevent duplicate attendance
7. Record attendance

---

## Phase 4: Reporting Phase

### Report Generation
1. Lecturer or Admin selects a session
2. System generates attendance report containing:
   - List of all students in target program/stream
   - Attendance status for each student
   - Timestamp of attendance (if marked)
   - Location data (if recorded)
3. Report can be exported in CSV or Excel format

### Report Storage
- Report metadata stored in database
- Physical file saved to designated file path
- Audit trail maintained (who generated, when generated)

---

## Workflow Summary Diagram

```
Admin Registration
       ↓
[Students & Lecturers in Database]
       ↓
Lecturer Creates Session → System Emails Students
       ↓                           ↓
Session Active              Students Receive Link
       ↓                           ↓
Lecturer at Location        Students Open Page
       ↓                           ↓
[GPS Location Stored]       Students Scan QR Code
       ↓                           ↓
                System Validates Location & Identity
                           ↓
                  Attendance Recorded
                           ↓
                  Reports Generated
```

---

## Key Workflow Principles

1. **No Student Authentication Required**
   - Students access via email link only
   - No login credentials needed for attendance

2. **Location-Based Validation**
   - Both lecturer and student locations captured
   - 30-meter radius strictly enforced

3. **One Attendance Per Session**
   - Database constraint prevents duplicates
   - Students cannot mark attendance multiple times

4. **Automated Communications**
   - Email notifications sent automatically (triggered when a lecturer creates a session)
   - No manual intervention required

5. **Audit Trail Throughout**
   - All actions timestamped
   - Location data preserved
   - Report generation tracked