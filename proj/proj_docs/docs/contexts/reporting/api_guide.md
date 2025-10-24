# api_guide.md

Brief: Complete API specification for Reporting context. Four REST endpoints with JWT Bearer authentication for report generation, viewing, export, and download. Focus on authorization (lecturer vs admin), request/response DTOs, file downloads, and comprehensive error handling.

---

## API Layer Purpose

**Why API Matters**:
- **Lecturer/Admin endpoints**: Report generation and viewing
- **JWT Bearer authentication**: Standard authorization header
- **File download support**: Serve exported CSV/Excel files
- **Authorization boundaries**: Lecturer sees own sessions, admin sees all
- **RESTful design**: Standard HTTP methods and status codes

**Priority: CRITICAL** - User interface for reporting

---

# AUTHENTICATION MODEL

## JWT Bearer Authentication

**How It Works**:
1. User logs in → receives JWT token
2. Include token in Authorization header: `Authorization: Bearer <token>`
3. Backend validates token, extracts user_id and role
4. Endpoints check role-based permissions

**Why JWT Bearer**:
- Standard authentication pattern
- Stateless (no server sessions)
- Role information in token payload
- Works for both lecturer and admin

**Token Payload**:
```json
{
  "user_id": 10,
  "role": "lecturer",  // or "admin"
  "exp": 1729342800
}
```

**Priority: CRITICAL** - Security foundation

---

# ENDPOINTS

## 1. POST /api/v1/sessions/{session_id}/report/

**Purpose**: Generate new attendance report (view-only, no export)

**Method**: POST (creates new Report record)

**Authentication**: JWT Bearer (required)

**Authorization**:
- **Lecturer**: Can generate for own sessions only
- **Admin**: Can generate for any session

**Priority: CRITICAL** - Primary endpoint

---

### Request Format

**URL Parameters**:
- `session_id` (integer): Session to generate report for

**Request Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Request Body**: None (GET-like POST for resource creation)

**Why POST (Not GET)**:
- Creates new Report record in database
- Not idempotent (each call creates new report)
- RESTful convention for resource creation

---

### Success Response (201 Created)

**Status Code**: 201 Created

**Response Body**:
```json
{
  "success": true,
  "data": {
    "report_id": 101,
    "session": {
      "session_id": 456,
      "course_name": "Data Structures",
      "course_code": "CSC201",
      "program_name": "Computer Science",
      "program_code": "BCS",
      "stream_name": "Stream A",
      "time_created": "2025-10-19T08:00:00Z",
      "time_ended": "2025-10-19T10:00:00Z",
      "lecturer_name": "Dr. Jane Smith"
    },
    "statistics": {
      "total_students": 50,
      "present_count": 35,
      "present_percentage": 70.0,
      "absent_count": 15,
      "absent_percentage": 30.0,
      "within_radius_count": 40,
      "outside_radius_count": 3
    },
    "students": [
      {
        "student_id": "BCS/234344",
        "student_name": "John Doe",
        "email": "john@example.com",
        "program": "Computer Science",
        "stream": "Stream A",
        "status": "Present",
        "time_recorded": "2025-10-19T08:05:23Z",
        "within_radius": true,
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
        "time_recorded": null,
        "within_radius": null,
        "latitude": null,
        "longitude": null
      }
      // ... more students
    ],
    "generated_date": "2025-10-19T14:30:22Z",
    "generated_by": "Dr. Jane Smith",
    "export_status": "not_exported"
  }
}
```
  Important: Official classification rule

   - A student is classified as "Present" in the `status` field only when ALL of the following are true:
     1. An attendance record exists for that student for the session.
     2. The attendance `time_recorded` is within the session window (>= `time_created` and <= `time_ended`).
     3. `within_radius` is `true` for that attendance record.

   - Any attendance records that fail either the time-window check or the radius check are retained in the `students` rows for diagnostics (you will still see `time_recorded`, `within_radius`, `latitude`, `longitude`) but such records DO NOT count toward the official `present_count` in `statistics`. Use `within_radius` and `time_recorded` for diagnostic filtering if you need to reconcile records.

   - In short: present_count = number of distinct students with at least one attendance record meeting (time window AND within_radius==true). Other counts such as `within_radius_count` are diagnostic and may differ from `present_count`.

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `report_id` | integer | Primary key of created report |
| `session` | object | Session details |
| `statistics` | object | Summary counts and percentages |
| `students` | array | List of student attendance rows |
| `export_status` | string | "not_exported" or "exported" |

**Why 201 Created**: New Report record created in database

---

### Error Responses

#### 401 Unauthorized - Missing/Invalid Token

**Scenario**: No Authorization header or invalid JWT

**Response**:
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required. Please provide a valid token."
  }
}
```

---

#### 403 Forbidden - Authorization Failed

**Scenario**: Lecturer trying to generate report for another lecturer's session

**Response**:
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "You do not have permission to generate reports for this session.",
    "details": {
      "session_id": 456,
      "session_lecturer": "Dr. John Smith",
      "requested_by": "Dr. Jane Doe"
    }
  }
}
```

**Why 403 (Not 401)**:
- User is authenticated (token valid)
- Authorization failed (not session owner)

---

#### 404 Not Found - Session Doesn't Exist


Notes on `statistics` fields:

- `present_count`: official count of students classified as Present under the canonical rule (attendance exists AND time within session window AND `within_radius` == true).
- `within_radius_count`: diagnostic count of attendance records with `within_radius` == true (may include records outside the session time window).
- `outside_radius_count`: diagnostic count of attendance records with `within_radius` == false.

**Scenario**: Invalid session_id

**Response**:
```json
{
  "success": false,
  "error": {
    "code": "SESSION_NOT_FOUND",
    "message": "Session not found.",
    "details": {
      "session_id": 999
    }
  }
}
```

---

## 2. GET /api/v1/reports/{report_id}/

**Purpose**: View existing report data

**Method**: GET

**Authentication**: JWT Bearer (required)

**Authorization**:
- **Lecturer**: Can view reports for own sessions only
- **Admin**: Can view all reports

**Priority: HIGH** - View historical reports

---

### Request Format

**URL Parameters**:
- `report_id` (integer): Report to view

**Request Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

### Success Response (200 OK)

**Status Code**: 200 OK

**Response Body**: Same structure as POST `/sessions/{id}/report/` response

**Note**: Data is re-queried (reflects current state, not snapshot)

---

### Error Responses

**401 Unauthorized**: Missing/invalid token (same as POST)

**403 Forbidden**: User cannot access this report

**404 Not Found**: Report doesn't exist

---

## 3. POST /api/v1/reports/{report_id}/export/

**Purpose**: Export report to CSV or Excel file

**Method**: POST (creates file, updates Report record)

**Authentication**: JWT Bearer (required)

**Authorization**:
- **Lecturer**: Can export reports for own sessions
- **Admin**: Can export any report

**Priority: CRITICAL** - File export

---

### Request Format

**URL Parameters**:
- `report_id` (integer): Report to export

**Request Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

**Request Body**:
```json
{
  "file_type": "csv"  // or "excel"
}
```

**Field Validation**:
- `file_type` (string, required): Must be "csv" or "excel"

---

### Success Response (200 OK)

**Status Code**: 200 OK

**Response Body**:
```json
{
  "success": true,
  "data": {
    "report_id": 101,
    "file_path": "/media/reports/2025/10/session_456_20251019143022.csv",
    "file_type": "csv",
    "download_url": "/api/v1/reports/101/download/",
    "generated_date": "2025-10-19T14:30:22Z"
  },
  "message": "Report exported successfully. Click download link to retrieve file."
}
```

**Why 200 OK (Not 201)**:
- Updates existing Report record (not creating new resource)
- File created, but primary resource is Report update

---

### Error Responses

**400 Bad Request - Invalid File Type**

**Scenario**: `file_type` not "csv" or "excel"

**Response**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_FILE_TYPE",
    "message": "File type must be 'csv' or 'excel'.",
    "details": {
      "provided_file_type": "pdf",
      "allowed_types": ["csv", "excel"]
    }
  }
}
```

---

**409 Conflict - Report Already Exported**

**Scenario**: Report already has file_path (prevent re-export)

**Response**:
```json
{
  "success": false,
  "error": {
    "code": "REPORT_ALREADY_EXPORTED",
    "message": "This report has already been exported. Use the download link to retrieve the file.",
    "details": {
      "report_id": 101,
      "existing_file_type": "csv",
      "download_url": "/api/v1/reports/101/download/"
    }
  }
}
```

**Why 409 Conflict**: Attempting to modify immutable resource

**Priority: HIGH** - Enforce immutability

---

**500 Internal Server Error - File Generation Failed**

**Scenario**: File I/O error, disk full, permissions issue

**Response**:
```json
{
  "success": false,
  "error": {
    "code": "EXPORT_FAILED",
    "message": "Failed to generate export file. Please try again or contact support.",
    "details": {
      "request_id": "req_xyz123"
    }
  }
}
```

**Security**: Never expose internal file paths or stack traces

---

## 4. GET /api/v1/reports/{report_id}/download/

**Purpose**: Download exported file (CSV or Excel)

**Method**: GET

**Authentication**: JWT Bearer (required)

**Authorization**: Same as view report (lecturer vs admin)

**Priority: HIGH** - File delivery

---

### Request Format

**URL Parameters**:
- `report_id` (integer): Report to download

**Request Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

### Success Response (200 OK)

**Status Code**: 200 OK

**Response Headers**:
```
Content-Type: text/csv  (for CSV) or application/vnd.openxmlformats-officedocument.spreadsheetml.sheet (for Excel)
Content-Disposition: attachment; filename="session_456_20251019143022.csv"
Content-Length: 15432
```

**Response Body**: Binary file content (CSV or Excel)

**Why Content-Disposition**: Forces browser to download (not display)

**Priority: CRITICAL** - File delivery mechanism

---

### Error Responses

**404 Not Found - Report Not Exported**

**Scenario**: Report exists but file_path is NULL (not exported)

**Response**:
```json
{
  "success": false,
  "error": {
    "code": "FILE_NOT_AVAILABLE",
    "message": "This report has not been exported. Please export the report first.",
    "details": {
      "report_id": 101,
      "export_url": "/api/v1/reports/101/export/"
    }
  }
}
```

---

**404 Not Found - File Missing**

**Scenario**: Report has file_path but file doesn't exist on disk (deleted manually)

**Response**:
```json
{
  "success": false,
  "error": {
    "code": "FILE_MISSING",
    "message": "Export file not found. Please regenerate the export.",
    "details": {
      "report_id": 101
    }
  }
}
```

---

## 5. GET /api/v1/reports/ (Admin Only)

**Purpose**: List all reports (admin monitoring)

**Method**: GET

**Authentication**: JWT Bearer (required)

**Authorization**: Admin only

**Priority: MEDIUM** - Admin dashboard

---

### Request Format

**Query Parameters** (optional):
- `session_id` (integer): Filter by session
- `user_id` (integer): Filter by user
- `start_date` (ISO 8601): Date range start
- `end_date` (ISO 8601): Date range end
- `page` (integer): Pagination (default 1)
- `page_size` (integer): Items per page (default 20)

**Example**: `/api/v1/reports/?session_id=456&page=2`

---

### Success Response (200 OK)

**Response Body**:
```json
{
  "success": true,
  "data": {
    "reports": [
      {
        "report_id": 101,
        "session_id": 456,
        "session_name": "Data Structures - CSC201",
        "generated_by": "Dr. Jane Smith",
        "generated_date": "2025-10-19T14:30:22Z",
        "export_status": "exported",
        "file_type": "csv"
      },
      // ... more reports
    ],
    "pagination": {
      "current_page": 2,
      "total_pages": 5,
      "total_reports": 97,
      "page_size": 20
    }
  }
}
```

---

### Error Responses

**403 Forbidden - Not Admin**

**Scenario**: Lecturer trying to access endpoint

**Response**:
```json
{
  "success": false,
  "error": {
    "code": "ADMIN_ONLY",
    "message": "This endpoint is restricted to administrators."
  }
}
```

---

# ERROR CODE REFERENCE

| Error Code | HTTP Status | Scenario |
|------------|-------------|----------|
| `UNAUTHORIZED` | 401 | Missing/invalid token |
| `FORBIDDEN` | 403 | Not authorized for session |
| `ADMIN_ONLY` | 403 | Endpoint requires admin role |
| `SESSION_NOT_FOUND` | 404 | Invalid session_id |
| `REPORT_NOT_FOUND` | 404 | Invalid report_id |
| `FILE_NOT_AVAILABLE` | 404 | Report not exported |
| `FILE_MISSING` | 404 | File deleted from disk |
| `INVALID_FILE_TYPE` | 400 | file_type not csv/excel |
| `REPORT_ALREADY_EXPORTED` | 409 | Prevent re-export |
| `EXPORT_FAILED` | 500 | File generation error |

**Priority: CRITICAL** - Consistent error handling

---

# HANDLER LAYER STRUCTURE

## File Organization

**Priority: MEDIUM** - Maintainability

```
reporting/
├── handlers/
│   ├── __init__.py
│   ├── generate_report_handler.py    # POST /sessions/{id}/report/
│   ├── view_report_handler.py        # GET /reports/{id}/
│   ├── export_report_handler.py      # POST /reports/{id}/export/
│   └── download_report_handler.py    # GET /reports/{id}/download/
│
├── services/
│   ├── report_service.py
│   └── export_service.py
│
├── views.py                          # Django view wrappers
├── urls.py                           # URL routing
├── serializers.py                    # Request/response validation
└── permissions.py                    # IsLecturerOrAdmin, IsReportOwner
```

**Why Separate Handlers**:
- Each handler <100 lines
- Clear single responsibility
- Easy to test independently
- Follows endpoint structure

---

## Serializers (Django REST Framework)

### GenerateReportRequestSerializer

**Purpose**: Validate report generation (no body, just URL param)

**Note**: Minimal validation (session_id from URL)

---

### ExportReportRequestSerializer

**Purpose**: Validate export request

**Fields**:
- `file_type` (CharField, required, choices=["csv", "excel"])

**Validation**:
```python
def validate_file_type(self, value):
    if value not in ["csv", "excel"]:
        raise ValidationError("file_type must be 'csv' or 'excel'")
    return value
```

---

### ReportResponseSerializer

**Purpose**: Format report data for API response

**Fields**:
- `report_id` (IntegerField)
- `session` (nested object)
- `statistics` (nested object)
- `students` (list of dicts)
- `generated_date` (DateTimeField, ISO 8601)
- `generated_by` (CharField)
- `export_status` (CharField)

---

## URL Routing

**File**: `urls.py`

```python
urlpatterns = [
    # Generate report
    path('sessions/<int:session_id>/report/', GenerateReportView.as_view(), name='generate_report'),
    
    # View report
    path('reports/<int:report_id>/', ViewReportView.as_view(), name='view_report'),
    
    # Export report
    path('reports/<int:report_id>/export/', ExportReportView.as_view(), name='export_report'),
    
    # Download report
    path('reports/<int:report_id>/download/', DownloadReportView.as_view(), name='download_report'),
    
    # List reports (admin)
    path('reports/', ListReportsView.as_view(), name='list_reports'),
]
```

**Why Nested Routes**:
- `/sessions/{id}/report/` - Report belongs to session context
- `/reports/{id}/` - Report is standalone resource

---

# PERMISSIONS (Django REST Framework)

## IsLecturerOrAdmin

**Purpose**: Ensure user is lecturer or admin (not student)

**Check**:
```python
return request.user.role in ["lecturer", "admin"]
```

**Applied To**: All endpoints

---

## IsSessionOwnerOrAdmin

**Purpose**: Ensure lecturer owns session or user is admin

**Check**:
```python
if request.user.role == "admin":
    return True
session = Session.objects.get(pk=session_id)
return session.lecturer_id == request.user.id
```

**Applied To**: Generate report endpoint

---

## IsReportOwnerOrAdmin

**Purpose**: Ensure report is for user's session or user is admin

**Check**:
```python
if request.user.role == "admin":
    return True
report = Report.objects.select_related('session').get(pk=report_id)
return report.session.lecturer_id == request.user.id
```

**Applied To**: View, export, download endpoints

---

# FILE DOWNLOAD IMPLEMENTATION

## Django File Response

**Purpose**: Serve file with correct headers

**Example**:
```python
from django.http import FileResponse
import os

file_path = report.file_path
filename = os.path.basename(file_path)

if report.file_type == "csv":
    content_type = "text/csv"
elif report.file_type == "excel":
    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

response = FileResponse(open(file_path, 'rb'), content_type=content_type)
response['Content-Disposition'] = f'attachment; filename="{filename}"'
return response
```

**Why Important**: Browser downloads file (not displays)

**Priority: HIGH**

---

# TESTING ENDPOINTS

## Manual Testing Checklist

**Generate Report**:
- ✅ 201 Created with report data
- ✅ 403 Forbidden for other lecturer's session
- ✅ 404 for invalid session

**View Report**:
- ✅ 200 OK with report data
- ✅ 403 for unauthorized user
- ✅ 404 for invalid report

**Export Report**:
- ✅ 200 OK with download URL
- ✅ 400 for invalid file_type
- ✅ 409 if already exported
- ✅ File created on disk

**Download Report**:
- ✅ 200 OK with file content
- ✅ Correct Content-Type and Content-Disposition headers
- ✅ 404 if not exported

**List Reports (Admin)**:
- ✅ 200 OK with paginated list
- ✅ 403 for non-admin

**Priority: HIGH** - Cover all scenarios

---

# API SUMMARY

## Endpoint Inventory

| Endpoint | Method | Auth | Purpose | Priority |
|----------|--------|------|---------|----------|
| `/sessions/{id}/report/` | POST | JWT Bearer | Generate report | CRITICAL |
| `/reports/{id}/` | GET | JWT Bearer | View report | HIGH |
| `/reports/{id}/export/` | POST | JWT Bearer | Export to file | CRITICAL |
| `/reports/{id}/download/` | GET | JWT Bearer | Download file | HIGH |
| `/reports/` | GET | JWT Bearer (Admin) | List all reports | MEDIUM |

---

## Key Takeaways

1. **JWT Bearer authentication** - Standard Authorization header
2. **Role-based authorization** - Lecturer vs admin permissions
3. **RESTful design** - Standard HTTP methods and status codes
4. **File download support** - Proper headers for CSV/Excel
5. **Immutability enforcement** - 409 Conflict on re-export
6. **Comprehensive errors** - Clear codes and messages
7. **Pagination** - Admin list endpoint supports paging

---

**Status**: 📋 Complete API specification ready for implementation