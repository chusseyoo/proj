# testing_guide.md

Brief: Complete testing strategy for Reporting context. Six parts plus fixtures covering report generation, Present/Late/Absent classification, CSV/Excel export, file downloads, authorization (lecturer vs admin), and cross-context integration. Focus on business logic correctness and access control.

---

## Testing Strategy Overview

**Why Testing Critical**:
- **Classification logic**: Present/Late/Absent must be correct
- **Authorization**: Lecturer vs admin access boundaries
- **File generation**: CSV/Excel format correctness
- **Cross-context integration**: Session, User, Attendance data collection
- **Immutability**: Export once, prevent re-export

**Priority: CRITICAL** - Data accuracy and security

**Testing Framework**: pytest with Django test database

**Excluded Parts**:
- Part 7: Performance testing (out of scope)

---

# PART 1: MODEL TESTS

## Test File

**File**: `tests/test_models.py`

**Purpose**: Validate Report model constraints and relationships

**Priority: HIGH** - Foundation layer

---

## Test Cases

### test_create_report_view_only

**Purpose**: Create report without export (file_path and file_type NULL)

**Setup**:
- Create session and user (prerequisites)
- Create Report with session_id and generated_by

**Assertions**:
- Record created successfully
- `generated_date` auto-set to current time
- `file_path` is NULL
- `file_type` is NULL

**Why Important**: Baseline view-only report creation

---

### test_check_constraint_file_type_requires_path

**Purpose**: CHECK constraint enforces field synchronization

**Test Cases**:
1. Both NULL → Valid ✅
2. Both set → Valid ✅
3. file_type set, file_path NULL → Invalid ❌
4. file_path set, file_type NULL → Invalid ❌

**Expected**: CHECK constraint violation for invalid states

**Why Critical**: **Data integrity** - prevent inconsistent states

---

### test_cascade_delete_session

**Purpose**: Deleting session deletes all its reports

**Setup**:
- Create session
- Create 3 reports for session
- Delete session

**Expected**: All 3 reports also deleted

**Why Important**: Referential integrity, no orphaned reports

---

### test_protect_delete_user

**Purpose**: Cannot delete user with generated reports

**Setup**:
- Create user
- Create report with generated_by = user
- Attempt to delete user

**Expected**: ProtectedError (cannot delete)

**Why Important**: **Audit trail** - preserve who generated reports

---

### test_multiple_reports_same_session

**Purpose**: Multiple reports for same session allowed (no unique constraint)

**Setup**:
- Create session
- Create report 1 for session at time T1
- Create report 2 for session at time T2

**Expected**: Both reports created successfully (historical snapshots)

**Why Important**: Historical tracking

---

### test_file_path_max_length

**Purpose**: Validate VARCHAR(500) length

**Setup**:
- Create report with file_path of 500 characters

**Expected**: Saved successfully

**Why Important**: Ensure sufficient path length

---

# PART 2: REPOSITORY TESTS

## Test File

**File**: `tests/test_repositories.py`

**Purpose**: Validate repository methods and queries

**Priority: CRITICAL** - Data access correctness

---

## Test Cases

### test_create_report

**Purpose**: Basic repository create operation

**Setup**:
- Valid report data dict

**Assertions**:
- Record created and returned
- ID assigned

---

### test_get_by_id_with_select_related

**Purpose**: Query optimization check

**Setup**:
- Create report

**Assertions**:
- `get_by_id()` returns report
- Can access `report.session` without additional query
- Can access `report.generated_by` without additional query

**How to Test**: Use Django query counter (django-debug-toolbar or pytest-django)

**Why Important**: **Performance** - avoid N+1 queries

---

### test_update_export_details_success

**Purpose**: Update report with export file info

**Setup**:
- Create report (file_path and file_type NULL)
- Call `update_export_details(report_id, "/path/to/file.csv", "csv")`

**Assertions**:
- Report updated
- `file_path` set correctly
- `file_type` set correctly
- CHECK constraint passes

---

### test_update_export_details_already_exported

**Purpose**: Prevent re-export (immutability)

**Setup**:
- Create report with existing export
- Attempt to update again with different path/type

**Expected**: `ReportAlreadyExportedError` raised

**Why Important**: **Immutability enforcement**

---

### test_get_by_session

**Purpose**: Query all reports for session

**Setup**:
- Create 3 reports for session A
- Create 2 reports for session B

**Assertions**:
- `get_by_session(A)` returns 3 reports
- `get_by_session(B)` returns 2 reports
- Ordered by generated_date descending (newest first)

---

### test_get_by_user

**Purpose**: Query all reports by user

**Setup**:
- User A generates 4 reports
- User B generates 2 reports

**Assertions**:
- `get_by_user(A)` returns 4 reports
- `get_by_user(B)` returns 2 reports

---

### test_get_by_session_and_user

**Purpose**: Combined filter for access control

**Setup**:
- User A generates report for session 1
- User B generates report for session 1
- User A generates report for session 2

**Assertions**:
- `get_by_session_and_user(session_1, user_A)` returns 1 report
- `get_by_session_and_user(session_1, user_B)` returns 1 report

**Why Important**: **Authorization** - filter by ownership

---

### test_get_exported_reports

**Purpose**: Filter by export status

**Setup**:
- Create 3 reports with export (file_path NOT NULL)
- Create 2 reports without export (file_path NULL)

**Assertions**:
- `get_exported_reports()` returns 3 reports

---

### test_get_all_reports_for_lecturer

**Purpose**: Lecturer sees reports for own sessions

**Setup**:
- Lecturer A owns session 1 and 2
- Lecturer B owns session 3
- Create reports for all sessions

**Assertions**:
- `get_all_reports_for_lecturer(A)` returns reports for sessions 1 and 2
- `get_all_reports_for_lecturer(B)` returns reports for session 3

**Why Critical**: **Access control** - boundary enforcement

---

### test_can_user_access_report_lecturer

**Purpose**: Authorization check for lecturer

**Setup**:
- Lecturer A owns session 1
- Report for session 1 exists
- Lecturer B tries to access

**Assertions**:
- `can_user_access_report(A, report_id)` returns True
- `can_user_access_report(B, report_id)` returns False

---

### test_can_user_access_report_admin

**Purpose**: Admin can access all reports

**Setup**:
- Report for any session
- Admin user

**Assertions**:
- `can_user_access_report(admin, report_id)` returns True

---

### test_get_session_details

**Purpose**: Cross-context data collection

**Setup**:
- Create session with course, program, stream, lecturer

**Assertions**:
- Returns dict with all session details
- Includes lecturer name
- Includes program and stream names

**Why Important**: Report header information

---

### test_get_eligible_students_with_stream

**Purpose**: Get students for stream-specific session

**Setup**:
- Session for BCS Stream A
- 10 students in BCS Stream A
- 5 students in BCS Stream B

**Assertions**:
- `get_eligible_students(session)` returns 10 students (Stream A only)

---

### test_get_eligible_students_without_stream

**Purpose**: Get students for program-wide session

**Setup**:
- Session for BCS (no stream)
- 10 students in BCS Stream A
- 5 students in BCS Stream B

**Assertions**:
- `get_eligible_students(session)` returns 15 students (all BCS)

**Why Important**: Accurate "Absent" student count

---

### test_get_attendance_for_session

**Purpose**: Cross-context attendance data

**Setup**:
- Session with 5 attendance records
- Create attendance records

**Assertions**:
- `get_attendance_for_session(session)` returns 5 records
- Includes student profile data (select_related)

---

### test_get_attendance_statistics

**Purpose**: Summary calculation

**Setup**:
- Session with 50 eligible students
- 35 marked "present"
- 8 marked "late"
- 7 did not attend (absent)

**Assertions**:
- `total_students` = 50
- `present_count` = 35, `present_percentage` = 70.0
- `late_count` = 8, `late_percentage` = 16.0
- `absent_count` = 7, `absent_percentage` = 14.0

**Why Important**: Report header summary

---

# PART 3: SERVICE TESTS

## Test File

**File**: `tests/test_services.py`

**Purpose**: Validate business logic in all three services

**Priority: CRITICAL** - Core functionality

---

## ReportService Tests

### test_generate_report_success

**Purpose**: Complete report generation workflow

**Setup**:
- Valid session, user (lecturer owns session)
- Eligible students and attendance data

**Assertions**:
- Report metadata created in database
- Returns complete report data (session, statistics, students)
- Statistics calculated correctly

**Why Important**: End-to-end happy path

---

### test_generate_report_unauthorized_lecturer

**Purpose**: Lecturer cannot generate for other's session

**Setup**:
- Session owned by Lecturer A
- Lecturer B attempts to generate report

**Expected**: `UnauthorizedReportAccessError` raised

**Why Critical**: **Access control enforcement**

---

### test_generate_report_admin_any_session

**Purpose**: Admin can generate for any session

**Setup**:
- Session owned by any lecturer
- Admin user generates report

**Expected**: Report generated successfully

---

### test_get_report_data_success

**Purpose**: Retrieve existing report

**Setup**:
- Create report
- Call `get_report_data(report_id, user_id)`

**Assertions**:
- Returns same structure as generate_report
- Data reflects current state (re-queried)

---

### test_get_report_data_unauthorized

**Purpose**: User cannot access other's reports

**Setup**:
- Report for Lecturer A's session
- Lecturer B tries to access

**Expected**: `UnauthorizedReportAccessError` raised

---

### test_validate_export_eligibility_not_exported

**Purpose**: Report can be exported (file_path NULL)

**Setup**:
- Report without export

**Expected**: Validation passes, returns Report

---

### test_validate_export_eligibility_already_exported

**Purpose**: Prevent re-export

**Setup**:
- Report with existing export

**Expected**: `ReportAlreadyExportedError` raised

**Why Important**: **Immutability enforcement**

---

## AttendanceAggregator Tests

### test_classify_students_all_present

**Purpose**: All students attended with valid attendance

**Setup**:
- 10 eligible students
- All 10 have attendance with status="present", is_within_radius=True

**Assertions**:
- All 10 classified as "Present"
- Time recorded included
- GPS coordinates included

---

### test_classify_students_some_absent

**Purpose**: Missing attendance classified as Absent

**Setup**:
- 10 eligible students
- 7 have attendance
- 3 do not have attendance

**Assertions**:
- 7 classified as "Present" or "Late"
- 3 classified as "Absent"
- Absent students have NULL time_recorded, within_radius, latitude, longitude

**Why Important**: **Core business logic** - Absent detection

---

### test_classify_single_student_present

**Purpose**: Present classification logic

**Setup**:
- Attendance with status="present", is_within_radius=True

**Expected**: `classify_single_student()` returns "Present"

---

### test_classify_single_student_late_status

**Purpose**: Late due to status field

**Setup**:
- Attendance with status="late", is_within_radius=True

**Expected**: Returns "Late"

---

### test_classify_single_student_late_location

**Purpose**: Late due to outside radius

**Setup**:
- Attendance with status="present", is_within_radius=False

**Expected**: Returns "Late"

**Why Important**: **Business rule** - Outside radius → Late

---

### test_classify_single_student_absent

**Purpose**: Absent classification

**Setup**:
- No attendance (None)

**Expected**: Returns "Absent"

---

### test_get_student_row_format

**Purpose**: Row data structure

**Setup**:
- Student with attendance

**Assertions**:
- Returns dict with all required fields
- student_id, student_name, email, program, stream
- status, time_recorded, within_radius, latitude, longitude

---

## ExportService Tests

### test_export_report_csv_success

**Purpose**: Complete CSV export workflow

**Setup**:
- Report without export
- Mock file system (or use temp directory)

**Workflow**:
1. Call `export_report(report_id, user_id, "csv")`
2. Check file created at correct path
3. Check report metadata updated (file_path, file_type)

**Assertions**:
- File exists on disk
- File contains correct CSV data
- Report updated with file_path and file_type="csv"

**Why Important**: End-to-end CSV export

---

### test_export_report_excel_success

**Purpose**: Complete Excel export workflow

**Setup**: Same as CSV test

**Assertions**:
- File exists with .xlsx extension
- Report updated with file_type="excel"

---

### test_export_report_unauthorized

**Purpose**: User cannot export other's reports

**Setup**:
- Report for Lecturer A's session
- Lecturer B attempts export

**Expected**: `UnauthorizedReportAccessError` raised

---

### test_export_report_already_exported

**Purpose**: Prevent re-export

**Setup**:
- Report already exported to CSV
- Attempt to export to Excel

**Expected**: `ReportAlreadyExportedError` raised

---

### test_generate_file_path_format

**Purpose**: File path format correctness

**Setup**:
- Session ID 456, current time 2025-10-19 14:30:22

**Expected Path**: `/media/reports/2025/10/session_456_20251019143022.csv`

**Assertions**:
- Year and month directories included
- Filename format: `session_{id}_{timestamp}.{ext}`
- Timestamp format: YYYYMMDDHHMMSS

**Why Important**: Organized storage, uniqueness

---

### test_generate_csv_file_content

**Purpose**: CSV file content correctness

**Setup**:
- Report data with students (Present, Late, Absent)

**Assertions**:
- Header row contains correct columns
- Data rows match student data
- Report header (comments) included
- Statistics summary included
- Absent students have empty fields for time/location

**Why Critical**: **Data accuracy**

---

### test_generate_csv_file_encoding

**Purpose**: Handle special characters (e.g., names with accents)

**Setup**:
- Student with name "José García"

**Assertions**:
- File saved with UTF-8 encoding
- Special characters preserved

---

### test_generate_excel_file_formatting

**Purpose**: Excel file has correct formatting

**Setup**:
- Report data with students

**Assertions**:
- Sheet 1 has report header
- Sheet 2 has attendance data
- Header row is bold
- Status cells color-coded (Present=Green, Late=Yellow, Absent=Red)
- Within Radius cells color-coded

**Why Important**: Professional presentation

---

### test_validate_file_type_invalid

**Purpose**: Reject invalid file types

**Setup**:
- file_type = "pdf"

**Expected**: `InvalidFileTypeError` raised

---

# PART 4: API/HANDLER TESTS

## Test File

**File**: `tests/test_handlers.py`

**Purpose**: HTTP layer testing

**Priority: HIGH** - User-facing interface

---

## Test Cases

### test_generate_report_success_201

**Purpose**: Valid request returns 201 Created

**Setup**:
- Authenticated lecturer
- Own session

**Assertions**:
- HTTP 201 status
- Response contains report_id, session, statistics, students
- `success=true`

---

### test_generate_report_unauthorized_401

**Purpose**: Missing token returns 401

**Setup**:
- No Authorization header

**Expected**: HTTP 401 Unauthorized

---

### test_generate_report_forbidden_403

**Purpose**: Lecturer for other's session returns 403

**Setup**:
- Lecturer B authenticated
- Session owned by Lecturer A

**Expected**: HTTP 403 Forbidden

---

### test_generate_report_session_not_found_404

**Purpose**: Invalid session returns 404

**Setup**:
- session_id = 999 (doesn't exist)

**Expected**: HTTP 404 Not Found

---

### test_view_report_success_200

**Purpose**: Valid request returns report data

**Setup**:
- Existing report
- Authorized user

**Expected**: HTTP 200 OK with report data

---

### test_export_report_csv_success_200

**Purpose**: Export creates file and returns download URL

**Setup**:
- Report without export
- Request with file_type="csv"

**Assertions**:
- HTTP 200 OK
- Response contains download_url
- File created on disk

---

### test_export_report_invalid_file_type_400

**Purpose**: Invalid file_type returns 400

**Setup**:
- file_type="pdf"

**Expected**: HTTP 400 Bad Request

---

### test_export_report_already_exported_409

**Purpose**: Re-export returns 409 Conflict

**Setup**:
- Report already exported

**Expected**: HTTP 409 Conflict with existing download_url

---

### test_download_report_success_200

**Purpose**: Download serves file with correct headers

**Setup**:
- Exported report (file exists)

**Assertions**:
- HTTP 200 OK
- Content-Type: text/csv or application/vnd...
- Content-Disposition: attachment with filename
- Response contains file content

---

### test_download_report_not_exported_404

**Purpose**: Download for non-exported report returns 404

**Setup**:
- Report without export (file_path NULL)

**Expected**: HTTP 404 Not Found with message to export first

---

### test_download_report_file_missing_404

**Purpose**: File deleted from disk returns 404

**Setup**:
- Report has file_path but file doesn't exist

**Expected**: HTTP 404 Not Found

---

### test_list_reports_admin_success_200

**Purpose**: Admin can list all reports

**Setup**:
- Admin user
- Multiple reports in database

**Assertions**:
- HTTP 200 OK
- Returns paginated list
- Includes reports from all users

---

### test_list_reports_lecturer_forbidden_403

**Purpose**: Lecturer cannot access admin endpoint

**Setup**:
- Lecturer user

**Expected**: HTTP 403 Forbidden

---

# PART 5: INTEGRATION TESTS

## Test File

**File**: `tests/test_integration.py`

**Purpose**: Cross-context and end-to-end workflows

**Priority: CRITICAL** - System integration

---

## Test Cases

### test_full_report_generation_workflow

**Purpose**: Complete workflow from session to download

**Workflow**:
1. Session Management: Create session
2. User Management: Create students
3. Attendance Recording: Mark attendance
4. Reporting: Generate report
5. Reporting: Export to CSV
6. Reporting: Download file

**Assertions**:
- Report data accurate (matches attendance)
- Statistics correct
- File downloadable

**Why Critical**: End-to-end integration validation

---

### test_cross_context_session_data

**Purpose**: Session details integrated correctly

**Setup**:
- Session with course, program, stream, lecturer
- Generate report

**Assertions**:
- Report includes course name, code
- Report includes program and stream names
- Report includes lecturer name

**Why Important**: Cross-context data consistency

---

### test_cross_context_student_data

**Purpose**: Student details integrated correctly

**Setup**:
- Students from User Management context
- Generate report

**Assertions**:
- Report includes student_id, name, email
- Report includes program and stream

---

### test_cross_context_attendance_data

**Purpose**: Attendance records integrated correctly

**Setup**:
- Attendance from Attendance Recording context
- Generate report

**Assertions**:
- Report includes time_recorded, status, is_within_radius
- Report includes GPS coordinates

---

### test_lecturer_access_control_boundary

**Purpose**: Lecturer cannot cross session boundaries

**Setup**:
- Lecturer A owns session 1
- Lecturer B owns session 2
- Reports for both sessions

**Assertions**:
- Lecturer A can only access session 1 reports
- Lecturer B can only access session 2 reports

**Why Critical**: **Security boundary enforcement**

---

### test_admin_can_access_all_sessions

**Purpose**: Admin has global access

**Setup**:
- Multiple lecturers with sessions
- Admin user

**Assertions**:
- Admin can generate reports for any session
- Admin can view all reports
- Admin can export any report

---

# PART 6: EDGE CASES AND ERROR SCENARIOS

## Test File

**File**: `tests/test_edge_cases.py`

**Purpose**: Unusual scenarios and boundary conditions

**Priority: HIGH** - Robustness

---

## Test Cases

### test_report_for_session_with_no_students

**Purpose**: Handle session with no eligible students

**Setup**:
- Session for program with no students

**Expected**: 
- Report generated successfully
- `total_students` = 0
- Empty students list
- Statistics all zeros

---

### test_report_for_session_with_no_attendance

**Purpose**: All students absent

**Setup**:
- Session with 10 eligible students
- No attendance records

**Assertions**:
- All 10 classified as "Absent"
- Statistics: absent_count=10, present_count=0, late_count=0

---

### test_report_for_session_with_all_late

**Purpose**: All students late (outside radius)

**Setup**:
- 10 students, all with is_within_radius=False

**Assertions**:
- All 10 classified as "Late"
- Statistics: late_count=10

---

### test_concurrent_report_generation

**Purpose**: Multiple reports for same session at same time

**Setup**:
- User generates report for session
- Immediately generate another report for same session

**Expected**: Both reports created successfully (historical snapshots)

---

### test_export_after_attendance_changes

**Purpose**: Export reflects current state (not snapshot)

**Setup**:
1. Generate report (5 students present)
2. Mark attendance for 5 more students
3. Export report

**Expected**: Export includes all 10 students (current state)

**Note**: Document behavior - not historical snapshot

---

### test_file_path_with_special_characters

**Purpose**: Handle edge cases in file paths

**Setup**:
- Session with unusual characters in name

**Assertions**:
- File path sanitized (no special chars)
- File created successfully

---

### test_csv_export_with_empty_fields

**Purpose**: Handle NULL values in CSV

**Setup**:
- Absent students (NULL time, location)

**Assertions**:
- CSV has empty cells (not "NULL" or "None")
- File parses correctly

---

### test_excel_export_with_large_dataset

**Purpose**: Handle many students (performance)

**Setup**:
- Session with 500 eligible students

**Assertions**:
- Excel file created successfully
- All students included
- File size reasonable

---

### test_download_concurrent_requests

**Purpose**: Multiple users downloading same file

**Setup**:
- Exported file
- Simulate concurrent download requests

**Expected**: All requests served successfully (file reading)

---

### test_file_system_error_handling

**Purpose**: Handle disk full or permissions errors

**Setup**:
- Mock file system to raise IOError

**Expected**: `FileGenerationError` raised, user-friendly message

---

### test_deleted_session_cascade

**Purpose**: Deleting session deletes reports and files

**Setup**:
- Session with exported reports
- Delete session

**Expected**:
- Report records deleted (CASCADE)
- Files remain on disk (manual cleanup or background job)

**Note**: Document file cleanup strategy

---

# PART 8: FIXTURES AND TEST DATA

## Test File

**File**: `tests/conftest.py`

**Purpose**: Reusable test data and setup

**Priority: MEDIUM** - Reduce duplication

---

## Fixtures

### sample_session

**Purpose**: Create session with all relationships

**Returns**: Session instance with course, program, stream, lecturer

---

### sample_lecturer

**Purpose**: Create lecturer user

**Returns**: User with role="lecturer"

---

### sample_admin

**Purpose**: Create admin user

**Returns**: User with role="admin"

---

### sample_students

**Purpose**: Create 10 student profiles

**Returns**: List of StudentProfile instances

---

### sample_attendance_records

**Purpose**: Create varied attendance (present, late, absent)

**Returns**: List of Attendance instances

**Breakdown**:
- 5 "present", is_within_radius=True
- 3 "late", is_within_radius=True
- 2 "present", is_within_radius=False (late due to location)

---

### sample_report

**Purpose**: Create report without export

**Returns**: Report instance

---

### sample_exported_report

**Purpose**: Create report with CSV export

**Returns**: Report instance with file_path and file_type set

---

### temp_export_directory

**Purpose**: Temporary directory for file tests

**Returns**: Path to temp directory

**Cleanup**: Delete after test

---

### mock_file_system

**Purpose**: Mock file operations for testing without disk I/O

**Returns**: Mock object for file operations

---

## Test Database Setup

**Django Test Database**:
- Separate test database
- Migrations applied
- Database wiped after each test

---

# TESTING SUMMARY

## Test Coverage Goals

| Component | Target Coverage | Priority |
|-----------|-----------------|----------|
| Models | 90%+ | HIGH |
| Repositories | 95%+ | CRITICAL |
| Services | 95%+ | CRITICAL |
| Handlers | 90%+ | HIGH |
| Integration | Key flows | CRITICAL |

---

## Critical Test Categories

**Priority: CRITICAL** - Must pass before deployment:
1. **Classification logic** - Present/Late/Absent accuracy
2. **Authorization** - Lecturer vs admin boundaries
3. **Cross-context integration** - Session, User, Attendance data
4. **File generation** - CSV/Excel format correctness
5. **Immutability** - Export once enforcement

**Priority: HIGH** - Important for robustness:
- File download headers
- Error response formatting
- Edge cases (no students, all absent)
- Statistics calculation

---

## Running Tests

**Command**: `pytest tests/reporting/`

**With Coverage**: `pytest --cov=reporting tests/reporting/`

**Single Test**: `pytest tests/reporting/test_services.py::test_classify_students_some_absent`

---

## Key Takeaways

1. **Classification logic testing** - Present/Late/Absent correctness critical
2. **Authorization testing** - Lecturer vs admin access boundaries
3. **File generation** - CSV and Excel format validation
4. **Cross-context integration** - Session, User, Attendance data accuracy
5. **Immutability enforcement** - Prevent re-export
6. **Edge cases** - No students, all absent, large datasets
7. **File download** - Headers and content type correctness
8. **Statistics accuracy** - Summary calculations verified

---

**Status**: 📋 Complete testing specification ready for implementation

**Test Count Estimate**: 80+ test cases across 6 parts + fixtures