# models_guide.md

Brief: Complete model specification for Reporting context. Report entity with nullable export fields, CHECK constraints, and CASCADE deletes. Focus on metadata storage with optional file export, access control relationships, and historical snapshot capability.

---

## Model Layer Purpose

**Why Models Matter**:
- **Metadata storage**: Track report generation (who, when, for which session)
- **Optional export**: File path and type nullable (view-only vs exported)
- **Historical snapshots**: Multiple reports per session allowed
- **Access control**: Link to generated_by user for ownership
- **Audit trail**: Immutable records of report generation

**Priority: CRITICAL** - Foundation for report tracking

---

# REPORT MODEL

## Overview

**Entity**: Report (primary entity in Reporting context)

**Purpose**: Store metadata about generated attendance reports, optionally track exported files

**File**: `models.py`

**Table Name**: `reports`

**Priority: CRITICAL** - Core entity

---

## Field Specifications

### report_id (Primary Key)

**Type**: Integer (SERIAL auto-increment)

**Constraints**:
- Primary Key
- Auto-increment
- NOT NULL (implicit)

**Why Important**: Unique identifier for each report generation

**Priority: HIGH**

---

### session_id (Foreign Key)

**Type**: Integer

**Constraints**:
- Foreign Key → `sessions.session_id`
- NOT NULL
- ON DELETE CASCADE
- Indexed

**Why CASCADE**: 
- If session deleted, all its reports should be deleted
- Reports are meaningless without session context
- Maintains referential integrity

**Why Important**: Links report to specific session

**Priority: CRITICAL** - Core relationship

**Cross-Context Integration**: Session Management context provides session details

---

### generated_by (Foreign Key)

**Type**: Integer

**Constraints**:
- Foreign Key → `users.user_id`
- NOT NULL
- ON DELETE PROTECT (cannot delete user with reports)
- Indexed

**Why PROTECT**: 
- Audit trail requires knowing who generated report
- Cannot orphan reports by deleting users
- Historical accountability

**Why Important**: **Access control** - determines report ownership

**Priority: CRITICAL** - Security and audit

**Access Rules**:
- Lecturer can view reports where `generated_by = lecturer_id` AND session belongs to lecturer
- Admin can view all reports

---

### generated_date (DateTime)

**Type**: DateTime (TIMESTAMPTZ with timezone)

**Constraints**:
- NOT NULL
- Auto-set on creation (default=NOW())
- Indexed

**Why Important**: 
- **Audit trail**: When report was generated
- **Historical tracking**: Multiple snapshots over time
- **Filtering**: Query reports by date range

**Priority: HIGH**

**Format**: ISO 8601 UTC timestamp (e.g., "2025-10-19T14:30:22.123Z")

---

### file_path (String, NULLABLE)

**Type**: String (VARCHAR(500))

**Constraints**:
- **NULLABLE** (default NULL)
- Maximum 500 characters
- Linked to file_type via CHECK constraint

**Values**:
- **NULL**: Report viewed online only (not exported)
- **Path string**: Exported file location (e.g., "/media/reports/2025/10/session_456_20251019143022.csv")

**Why Nullable**: 
- Not all reports are exported (view-only use case)
- Export is optional user action
- Allows report generation without immediate file creation

**Priority: HIGH** - Distinguishes view-only from exported reports

**Path Format**: Absolute or relative path within export directory

---

### file_type (Enum, NULLABLE)

**Type**: String (VARCHAR(10))

**Constraints**:
- **NULLABLE** (default NULL)
- CHECK constraint: `file_type IN ('csv', 'excel')`
- Linked to file_path via CHECK constraint

**Values**:
- **NULL**: No export (report viewed online only)
- **"csv"**: CSV format export
- **"excel"**: Excel (.xlsx) format export

**Why Nullable**: Aligned with file_path (both NULL for view-only)

**Priority: HIGH** - Determines export format

---

## Database Constraints

### CHECK Constraint: file_type_requires_path

**Purpose**: Ensure file_path and file_type are synchronized

**Logic**:
```sql
CHECK (
  (file_type IS NULL AND file_path IS NULL) OR 
  (file_type IS NOT NULL AND file_path IS NOT NULL)
)
```

**Why Critical**: 
- **Data integrity**: Can't have file_type without file_path
- **Consistency**: Both fields NULL or both fields set
- Prevents invalid states (e.g., "csv" type with no path)

**Valid States**:
- `file_type = NULL, file_path = NULL` ✅ (view-only report)
- `file_type = "csv", file_path = "/media/reports/..."` ✅ (CSV export)
- `file_type = "excel", file_path = "/media/reports/..."` ✅ (Excel export)

**Invalid States**:
- `file_type = "csv", file_path = NULL` ❌ (type without path)
- `file_type = NULL, file_path = "/media/reports/..."` ❌ (path without type)

**Priority: CRITICAL** - Prevents data corruption

---

## Indexes

### idx_reports_session_id

**Column**: session_id

**Why Important**: Fast queries for "all reports for session X"

**Use Case**: Lecturer views report history for a session

**Priority: HIGH**

---

### idx_reports_generated_by

**Column**: generated_by

**Why Important**: Fast queries for "all reports by user Y"

**Use Case**: User dashboard showing their generated reports

**Priority: HIGH**

---

### idx_reports_generated_date

**Column**: generated_date

**Why Important**: 
- Date range queries (e.g., "reports from last month")
- Sorting by generation date (newest first)

**Use Case**: Admin report monitoring, cleanup of old reports

**Priority: MEDIUM**

---

## Unique Constraints

**None Required**

**Why**: 
- Multiple reports for same session allowed (historical snapshots)
- Same user can generate multiple reports for same session
- Each generation creates new record

**Example Valid Scenario**:
```
Report 1: session_id=456, generated_by=10, generated_date=2025-10-19 10:00
Report 2: session_id=456, generated_by=10, generated_date=2025-10-19 14:30
Both valid - two snapshots of same session by same user
```

---

## Default Values

| Field | Default Value | Why |
|-------|---------------|-----|
| generated_date | NOW() | Auto-timestamp on creation |
| file_path | NULL | No export by default |
| file_type | NULL | No export by default |

---

## Validation Rules (Application Layer)

### On Report Creation (View-Only)

**Required Fields**:
- session_id (must exist in sessions table)
- generated_by (must exist in users table)

**Nullable Fields**:
- file_path (NULL)
- file_type (NULL)

**Authorization Check**:
- If user is lecturer: session.lecturer_id must equal generated_by
- If user is admin: no restriction

---

### On Report Export (Update Operation)

**Update Fields**:
- file_path (NULL → path string)
- file_type (NULL → "csv" or "excel")

**Validation**:
- Both fields updated together (atomic operation)
- file_path must be valid file system path
- file_path must be within designated export directory
- file_type must be "csv" or "excel"

**Side Effect**: File created in file system at file_path

---

## Immutability Rules

**Immutable Fields** (cannot change after creation):
- report_id
- session_id
- generated_by
- generated_date

**Mutable Fields** (can change once from NULL):
- file_path (NULL → path, but not path → different path)
- file_type (NULL → "csv"/"excel", but not "csv" → "excel")

**Why Partial Immutability**:
- Report metadata is immutable (audit trail)
- Export details set once (on first export)
- Cannot re-export to different format (prevents confusion)

**Priority: HIGH** - Maintain historical integrity

---

## Model Relationships

### Outbound Foreign Keys

```
Report
  ├── session_id → Session (Session Management context)
  │   └── ON DELETE CASCADE
  │
  └── generated_by → User (User Management context)
      └── ON DELETE PROTECT
```

**Why CASCADE for session**: Reports are session-dependent

**Why PROTECT for user**: Audit trail requires user identity preservation

---

### Inbound Relationships

**None** - Report is a leaf entity (no other entities reference it)

---

## Cross-Context Integration Points

### Session Management Context

**Dependency**: Get session details for report

**Data Needed**:
- Course name and code
- Program and stream
- Session date, time_created, time_ended
- Lecturer name

**Query Example**: `session = Session.objects.get(pk=session_id)`

---

### User Management Context

**Dependency**: Get user details

**Data Needed**:
- User name (for "Generated By" field)
- User role (for authorization)
- Eligible students list (by program/stream)

**Query Example**: `students = StudentProfile.objects.filter(program=session.program)`

---

### Attendance Recording Context

**Dependency**: Get attendance records for session

**Data Needed**:
- Student attendance existence (for Present/Absent classification)
- Attendance details (time_recorded, status, is_within_radius)

**Query Example**: `attendance = Attendance.objects.filter(session=session)`

---

## File Organization

**Priority: MEDIUM** - Maintainability

```
reporting/
├── models.py                    # Report model defined here
│   └── class Report(models.Model):
│       ├── report_id (AutoField)
│       ├── session_id (ForeignKey)
│       ├── generated_by (ForeignKey)
│       ├── generated_date (DateTimeField)
│       ├── file_path (CharField, null=True)
│       └── file_type (CharField, null=True)
│
├── migrations/
│   └── 0001_initial.py          # Initial migration with CHECK constraint
│
└── tests/
    └── test_models.py           # Model validation tests
```

---

## Business Rules Enforced at Model Level

### 1. Report Metadata Always Stored

**Rule**: Every report generation creates a Report record

**Enforcement**: NOT NULL constraints on session_id, generated_by, generated_date

**Why**: Audit trail of all report generations

---

### 2. Export is Optional

**Rule**: Reports can be viewed without exporting

**Enforcement**: Nullable file_path and file_type

**Why**: Reduces unnecessary file storage

---

### 3. Export Consistency

**Rule**: File path and type must be synchronized

**Enforcement**: CHECK constraint `file_type_requires_path`

**Why**: Prevents invalid states (type without path or vice versa)

---

### 4. Session Deletion Cascades

**Rule**: Deleting session deletes all its reports

**Enforcement**: ON DELETE CASCADE on session_id FK

**Why**: Reports are meaningless without session context

---

### 5. User Deletion Protected

**Rule**: Cannot delete user who has generated reports

**Enforcement**: ON DELETE PROTECT on generated_by FK

**Why**: Preserve audit trail (who generated what)

---

## Usage Examples (Conceptual)

### Create View-Only Report

```python
# User generates report and views online (no export)
report = Report(
    session_id=456,
    generated_by=10,
    # generated_date auto-set
    # file_path=NULL (default)
    # file_type=NULL (default)
)
# Valid: Both file_path and file_type are NULL
```

---

### Export Report to CSV

```python
# User exports existing report
report.file_path = "/media/reports/2025/10/session_456_20251019143022.csv"
report.file_type = "csv"
# Valid: Both fields set together (CHECK constraint passes)
```

---

### Invalid State (Prevented by CHECK)

```python
# Attempt to set only file_type
report.file_type = "csv"
# file_path still NULL
# CHECK constraint violation → Database error
```

---

## Model Summary

**Report Entity**:
- **Purpose**: Metadata for attendance reports
- **Key Feature**: Nullable export fields (view-only vs exported)
- **Relationships**: Session (CASCADE), User (PROTECT)
- **Constraints**: CHECK for file_path/file_type synchronization
- **Indexes**: session_id, generated_by, generated_date
- **Immutability**: Metadata immutable, export details set once

---

## Key Takeaways

1. **Nullable export fields** - file_path and file_type both NULL or both set
2. **CHECK constraint** - Enforces field synchronization
3. **CASCADE delete** - Session deletion removes reports
4. **PROTECT delete** - User deletion blocked if reports exist
5. **Historical snapshots** - Multiple reports per session allowed
6. **Access control** - generated_by links to user for ownership
7. **Partial immutability** - Metadata fixed, export details set once

---

**Status**: 📋 Complete model specification ready for implementation

**Priority Fields**:
- CRITICAL: session_id, generated_by (relationships and authorization)
- HIGH: file_path, file_type (nullable export mechanism)
- HIGH: generated_date (audit trail)
- MEDIUM: Indexes (performance)