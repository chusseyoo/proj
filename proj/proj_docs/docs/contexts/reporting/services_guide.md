# services_guide.md

Brief: Complete service specification for Reporting context. Three focused services: ReportService (orchestration), AttendanceAggregator (classify Present/Absent), and ExportService (CSV/Excel generation). Focus on business logic, cross-context data collection, file generation, and access control validation.

---

## Service Layer Purpose

**Why Services Matter**:
- **Business logic**: Classify attendance status, calculate statistics
- **Orchestration**: Coordinate multiple repositories and contexts
- **File generation**: Create CSV/Excel exports with formatting
- **Authorization**: Enforce lecturer vs admin access rules
- **Data transformation**: Convert raw data to report format

**Priority: CRITICAL** - Core report generation logic

---

# SERVICE ARCHITECTURE

## Three Services Pattern

1. **ReportService** - Report generation orchestration and authorization
2. **AttendanceAggregator** - Classify students as Present/Absent
3. **ExportService** - CSV and Excel file generation

**Why Separate**:
- Single responsibility per service
- AttendanceAggregator reusable for dashboards
- ExportService testable independently (mock file I/O)
- ReportService coordinates workflow

---

# PART 1: REPORTSERVICE

## Overview

**File**: `services/report_service.py`

**Purpose**: Orchestrate report generation, enforce authorization, create metadata

**Dependencies**:
- ReportRepository
- AttendanceAggregator (internal service)
- Authorization logic

**Priority: CRITICAL** - Main orchestrator

---

## Method Specifications

### generate_report(session_id: int, user_id: int) → dict

**Purpose**: Generate attendance report (view-only, no file export)

**Workflow**:

1. **Authorization Check**
   ```python
   if not report_repo.can_user_generate_report_for_session(user_id, session_id):
       raise UnauthorizedReportAccessError("Cannot generate report for this session")
   ```

2. **Collect Session Details**
   ```python
   session_details = report_repo.get_session_details(session_id)
   ```

3. **Get Eligible Students**
   ```python
   eligible_students = report_repo.get_eligible_students(session_id)
   ```

4. **Get Attendance Records**
   ```python
   attendance_records = report_repo.get_attendance_for_session(session_id)
   ```

5. **Classify Students** (using AttendanceAggregator)
   ```python
   student_rows = attendance_aggregator.classify_students(
       eligible_students, attendance_records
   )
   ```

6. **Calculate Statistics**
   ```python
   statistics = report_repo.get_attendance_statistics(session_id)
   ```

7. **Create Report Metadata**
   ```python
   report = report_repo.create({
       "session_id": session_id,
       "generated_by": user_id
   })
   ```

8. **Return Report Data**

**Returns**: Dictionary with report details:
```python
{
    "report_id": 101,
    "session": session_details,
    "statistics": statistics,
    "students": student_rows,  # List of student attendance rows
    "generated_date": "2025-10-19T14:30:22Z",
    "generated_by_name": "Dr. Jane Smith"
}
```

**Why Important**: Complete view-only report generation

**Priority: CRITICAL** - Core functionality

**Error Handling**:
- Session not found → `SessionNotFoundError`
- Unauthorized → `UnauthorizedReportAccessError`
- Database errors → Propagate

---

### get_report_data(report_id: int, user_id: int) → dict

**Purpose**: Retrieve existing report data (regenerate display from metadata)

**Workflow**:

1. **Get Report Metadata**
   ```python
   report = report_repo.get_by_id(report_id)
   if not report:
       raise ReportNotFoundError(f"Report {report_id} not found")
   ```

2. **Authorization Check**
   ```python
   if not report_repo.can_user_access_report(user_id, report_id):
       raise UnauthorizedReportAccessError("Cannot access this report")
   ```

3. **Regenerate Report Data** (same as generate_report)
   - Collect session details
   - Get eligible students
   - Get attendance records
   - Classify students
   - Calculate statistics

4. **Return Report Data**

**Returns**: Same structure as `generate_report`

**Why Important**: View historical reports (re-query data from snapshot time)

**Note**: Data reflects **current state**, not snapshot at generation time (unless implementing snapshot storage)

**Priority: HIGH**

---

### validate_export_eligibility(report_id: int, user_id: int) → Report

**Purpose**: Check if report can be exported

**Validations**:
1. Report exists
2. User authorized to access report
3. Report not already exported (file_path is NULL)

**Returns**: Report instance if valid

**Error Handling**:
- Report not found → `ReportNotFoundError`
- Unauthorized → `UnauthorizedReportAccessError`
- Already exported → `ReportAlreadyExportedError`

**Why Important**: Prevent re-export to different formats (immutability)

**Priority: HIGH**

---

## Authorization Logic

### Lecturer Authorization

**Rule**: Lecturer can only generate/view reports for own sessions

**Check**:
```python
session = Session.objects.get(pk=session_id)
if user.role == "lecturer" and session.lecturer_id != user_id:
    raise UnauthorizedReportAccessError()
```

**Why Important**: Data privacy, access control

---

### Admin Authorization

**Rule**: Admin can generate/view reports for any session

**Check**:
```python
if user.role == "admin":
    # Always authorized
    return True
```

**Why Important**: System monitoring, support

---

# PART 2: ATTENDANCEAGGREGATOR SERVICE

## Overview

**File**: `services/attendance_aggregator.py`

**Purpose**: Classify students as Present or Absent based on attendance data (retain diagnostics such as original status and within-radius flag)

**Dependencies**: None (pure logic)

**Priority: CRITICAL** - Core classification logic

---

## Method Specifications

### classify_students(eligible_students: QuerySet[StudentProfile], attendance_records: QuerySet[Attendance]) → list[dict]

**Purpose**: Create report rows with attendance classification

**Logic**:

1. **Create attendance lookup map**
   ```python
   attendance_map = {
       att.student_profile_id: att 
       for att in attendance_records
   }
   ```

2. **For each eligible student**:
    - Check if an attendance record exists in the lookup map
    - If an attendance record exists, verify both:
      - the attendance timestamp falls within the session time window, and
      - `is_within_radius` is True
      - If both are true → classify as **Present** (include time/location/status as diagnostics)
      - Otherwise → classify as **Absent** (the attendance record may be kept for audit/diagnostics but does not count as Present)
    - If no attendance record exists → classify as **Absent**

3. **Return list of student rows**

**Returns**: List of dictionaries:
```python
[
    {
        "student_id": "BCS/234344",
        "student_name": "John Doe",
        "email": "john@example.com",
        "program": "Computer Science",
        "stream": "Stream A",
        "status": "Present",
        "time_recorded": "2025-10-19T08:05:23Z",
        "within_radius": True,
        "latitude": "-1.28334000",
        "longitude": "36.81667000"
    },
    {
        "student_id": "BCS/234345",
        "student_name": "Jane Smith",
        "email": "jane@example.com",
        "program": "Computer Science",
        "stream": "Stream A",
        "status": "Absent",
        "time_recorded": None,
        "within_radius": None,
        "latitude": None,
        "longitude": None
    },
    # ...
]
```

**Why Important**: Determines final report content

**Priority: CRITICAL** - Core business logic

---

### classify_single_student(student: StudentProfile, attendance: Attendance | None, session_start: datetime, session_end: datetime) → str

**Purpose**: Determine a single student's presence classification using strict rules (time window + radius)

**Logic**:
```python
def classify_single_student(student, attendance, session_start, session_end):
    # No attendance record → Absent
    if attendance is None:
        return "Absent"

    # Attendance exists: check radius
    if not getattr(attendance, "is_within_radius", False):
        return "Absent"

    # Check attendance timestamp within session scheduled window
    att_ts = getattr(attendance, "timestamp", None) or getattr(attendance, "time_recorded", None)
    if att_ts is None:
        # Missing timestamp treated as Absent for official reporting
        return "Absent"

    if not (session_start <= att_ts <= session_end):
        return "Absent"

    # All checks passed → Present
    return "Present"
```

**Returns**: "Present" or "Absent"

**Classification Rules**:

| Attendance Exists | Within Time Window | is_within_radius | Final Status |
|-------------------|--------------------:|------------------:|--------------|
| No | - | - | **Absent** |
| Yes | No | any | **Absent** |
| Yes | Yes | False | **Absent** |
| Yes | Yes | True | **Present** |

**Why Important**: This enforces the policy that only attendances recorded within the scheduled session window and within the allowed GPS radius count as Present. Any other recorded attendance is treated as Absent for official reporting; such records can still be retained for diagnostics/audit.

**Priority: CRITICAL** - Business rule enforcement

---

### get_student_row(student: StudentProfile, attendance: Attendance | None) → dict

**Purpose**: Format single student row for report

**Returns**: Dictionary with student and attendance details (as shown in `classify_students`)

**Why Important**: Data transformation for export

**Priority: HIGH**

---

# PART 3: EXPORTSERVICE

## Overview

**File**: `services/export_service.py`

**Purpose**: Generate CSV and Excel files, update report metadata with file paths

**Dependencies**:
- ReportRepository
- ReportService (get report data)
- File system (write files)
- Python csv module (CSV export)
- openpyxl or xlsxwriter (Excel export)

**Priority: CRITICAL** - File generation

---

## Method Specifications

### export_report(report_id: int, user_id: int, file_type: str) → dict

**Purpose**: Complete export workflow

**Parameters**:
- report_id: Report to export
- user_id: User requesting export (authorization)
- file_type: "csv" or "excel"

**Workflow**:

1. **Validate Export Eligibility**
   ```python
   report = report_service.validate_export_eligibility(report_id, user_id)
   ```

2. **Get Report Data**
   ```python
   report_data = report_service.get_report_data(report_id, user_id)
   ```

3. **Generate File Path**
   ```python
   file_path = generate_file_path(report.session_id, file_type)
   # Example: "/media/reports/2025/10/session_456_20251019143022.csv"
   ```

4. **Generate File** (based on file_type)
   ```python
   if file_type == "csv":
       generate_csv_file(file_path, report_data)
   elif file_type == "excel":
       generate_excel_file(file_path, report_data)
   ```

5. **Update Report Metadata**
   ```python
   report_repo.update_export_details(report_id, file_path, file_type)
   ```

6. **Return Export Info**

**Returns**: Dictionary with export details:
```python
{
    "report_id": 101,
    "file_path": "/media/reports/2025/10/session_456_20251019143022.csv",
    "file_type": "csv",
    "download_url": "/api/v1/reports/101/download/"
}
```

**Why Important**: Complete export orchestration

**Priority: CRITICAL** - Core functionality

**Error Handling**:
- File I/O errors → Log and raise `ExportError`
- Validation errors → Propagate from report_service

---

### generate_file_path(session_id: int, file_type: str) → str

**Purpose**: Create unique file path for export

**File Naming Convention**:
```
session_{session_id}_{timestamp}.{extension}
```

**Directory Structure**:
```
/media/reports/{year}/{month}/
```

**Example**:
```
/media/reports/2025/10/session_456_20251019143022.csv
```

**Returns**: Absolute file path

**Why Important**: Organized storage, prevent overwrites

**Priority: HIGH**

**Timestamp Format**: `YYYYMMDDHHMMSS` (no separators)

---

### generate_csv_file(file_path: str, report_data: dict) → None

**Purpose**: Write CSV file to disk

**CSV Structure**:

**Header Row**:
```csv
Student ID,Student Name,Email,Program,Stream,Status,Time Recorded,Within Radius,Latitude,Longitude
```

**Data Rows** (from `report_data["students"]`):
```csv
BCS/234344,John Doe,john@example.com,Computer Science,Stream A,Present,2025-10-19 08:05:23,Yes,-1.28334000,36.81667000
BCS/234345,Jane Smith,jane@example.com,Computer Science,Stream A,Absent,,,,,
```

**Report Header** (comments at top):
```csv
# Session Report
# Session ID: 456
# Course: Data Structures (CSC201)
# Program: Computer Science (BCS) - Stream A
# Date: 2025-10-19 08:00-10:00
# Lecturer: Dr. Jane Smith
# Generated: 2025-10-19 14:30:22 by Dr. Jane Smith
# Total Students: 50 | Present: 35 (70%) | Absent: 15 (30%)
#
```

**Why Important**: Human-readable format, Excel import compatible

**Priority: CRITICAL**

**Implementation**: Python `csv.DictWriter`

---

### generate_excel_file(file_path: str, report_data: dict) → None

**Purpose**: Write Excel file with formatting

**Excel Structure**:

**Sheet 1: "Report Header"**
- Session details (same as CSV header, formatted as table)
- Statistics summary

**Sheet 2: "Attendance Data"**
- Header row (bold, background color)
- Data rows with conditional formatting:
    - "Present" → Green background
    - "Absent" → Red background
    - "Within Radius" column:
    - "Yes" → Green text
    - "No" → Red text

**Why Important**: Professional presentation, color-coded status

**Priority: HIGH**

**Implementation**: `openpyxl` library for .xlsx format

**Formatting Features**:
- Bold headers
- Auto-fit column widths
- Freeze top row
- Conditional formatting for status
- Cell borders

---

### validate_file_type(file_type: str) → None

**Purpose**: Ensure file_type is valid

**Validation**:
```python
if file_type not in ["csv", "excel"]:
    raise InvalidFileTypeError(f"Invalid file type: {file_type}")
```

**Why Important**: Prevent invalid formats

**Priority: MEDIUM**

---

## File System Operations

### Directory Creation

**Ensure directory exists before writing**:
```python
import os
os.makedirs(os.path.dirname(file_path), exist_ok=True)
```

**Why Important**: Prevent FileNotFoundError

---

### File Overwrite Prevention

**Check if file exists**:
```python
if os.path.exists(file_path):
    # This shouldn't happen with timestamp in filename
    raise FileExistsError(f"File already exists: {file_path}")
```

**Why Important**: Prevent data loss

---

### File Permissions

**Set appropriate permissions** (read-only for others):
```python
os.chmod(file_path, 0o644)  # rw-r--r--
```

**Why Important**: Security, prevent unauthorized modification

---

# SERVICE COLLABORATION PATTERN

## How Services Work Together

```
ReportService.generate_report()
    ↓ calls
ReportRepository.get_session_details()
ReportRepository.get_eligible_students()
ReportRepository.get_attendance_for_session()
    ↓ calls
AttendanceAggregator.classify_students()
    ↓ calls
ReportRepository.create()
    ↓ returns
Report data (view-only)

---

ExportService.export_report()
    ↓ calls
ReportService.validate_export_eligibility()
ReportService.get_report_data()
    ↓ calls
ExportService.generate_file_path()
ExportService.generate_csv_file() OR generate_excel_file()
    ↓ calls
ReportRepository.update_export_details()
    ↓ returns
Export info with download URL
```

**Why This Pattern**:
- ReportService focuses on data collection and orchestration
- AttendanceAggregator is pure logic (no dependencies)
- ExportService handles file generation and metadata update
- Clear separation of concerns

---

# ERROR HANDLING

## Domain Exceptions

**File**: `exceptions.py`

```python
class ExportError(Exception):
    """Base export exception"""
    pass

class InvalidFileTypeError(ExportError):
    """File type not csv or excel"""
    pass

class FileGenerationError(ExportError):
    """Error writing file"""
    pass

class ReportAlreadyExportedError(ExportError):
    """Report already has file_path"""
    pass
```

---

## File Organization

**Priority: MEDIUM** - Maintainability

```
reporting/
├── services/
│   ├── __init__.py
│   ├── report_service.py            # ReportService
│   ├── attendance_aggregator.py     # AttendanceAggregator
│   └── export_service.py            # ExportService
│
├── repositories/
│   └── report_repository.py
│
├── exceptions.py
│
└── tests/
    ├── test_report_service.py
    ├── test_attendance_aggregator.py
    └── test_export_service.py
```

**Why Three Service Files**:
- Clear separation of concerns
- Each file <300 lines (maintainable size)
- Easy to test independently
- Can extend with new export formats

---

## Service Summary

### ReportService (Orchestration)
- `generate_report` - Create view-only report
- `get_report_data` - Retrieve existing report
- `validate_export_eligibility` - Check before export

### AttendanceAggregator (Classification)
- `classify_students` - Bulk classification
- `classify_single_student` - Single student status
- `get_student_row` - Format row data

### ExportService (File Generation)
- `export_report` - Complete export workflow
- `generate_file_path` - Create unique path
- `generate_csv_file` - CSV export
- `generate_excel_file` - Excel export with formatting
- `validate_file_type` - Format validation

---

## Key Takeaways

1. **Three focused services** - Report, Aggregator, Export
2. **Clear classification rules** - Present/Absent logic (retain diagnostics)
3. **Authorization enforcement** - Lecturer vs admin access
4. **File generation** - CSV and Excel with formatting
5. **Orchestration pattern** - Coordinate multiple repos/contexts
6. **Immutability** - Export once, update metadata once
7. **Error handling** - Domain exceptions for all failures

---

**Status**: 📋 Complete service specification ready for implementation

**Priority Services**:
- CRITICAL: ReportService.generate_report, AttendanceAggregator.classify_students, ExportService.export_report
- HIGH: get_report_data, validate_export_eligibility, generate_csv_file, generate_excel_file
- MEDIUM: File path generation, file type validation