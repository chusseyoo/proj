# User Roles

## Role-Based Access Control

The system implements three distinct user roles with different permissions and capabilities.

---

## Admin Role

### Responsibilities
- System-wide management and configuration
- User account management
- Data integrity oversight
- System monitoring and reporting

### Permissions

#### User Management
- Manage lecturer accounts (deactivate/reactivate, modify details)
- Register and manage students
- Deactivate/reactivate user accounts
- Reset passwords
- Modify user information

#### Academic Structure Management
- Create and manage programs
- Create and manage streams
- Create and manage courses
- Assign courses to lecturers
- Configure program-stream relationships

#### Session Management
- View all sessions across the system
- Monitor session attendance
- Manage session data
- Note: Admins CANNOT create attendance sessions; only lecturers may create sessions for their courses

#### Reporting
- Generate reports for any session
- View comprehensive system reports
- Export data in CSV/Excel formats
- Access audit logs

#### System Configuration
- Configure system settings
- Manage email templates
- Set system-wide parameters (e.g., proximity radius)

### Access Level
**Full System Access** - Admins have unrestricted access to all system features and data (except creating lecturer accounts or creating attendance sessions).

---

## Lecturer Role

### Responsibilities
- Course and session management
- Attendance tracking and verification
- Student attendance reporting

### Permissions

#### Course Management
- Create and manage own courses
- View course enrollment
- Access course-related reports

#### Session Management
- Create attendance sessions for own courses
- Specify session details (date, time, location, target program/stream)
- View session attendance in real-time
- End sessions manually or automatically

#### Attendance Management
- View attendance records for own sessions
- Generate attendance reports
- Export attendance data (CSV, Excel)

### Access Restrictions
- Cannot access other lecturers' courses or sessions
- Cannot manage user accounts
- Cannot modify system configuration
- Cannot access admin-level reports

### Account Lifecycle
- **Registration**: Self-register via web interface
- **Activation**: Automatically activated upon registration
- **Authentication**: Email and password required
- **Status**: Active by default; admin can deactivate if needed

---

## Student Role

### Authentication and accounts
- Students are registered by admins and have a StudentProfile record in the database.
- Students do NOT receive login credentials. The User.password field is left NULL for student accounts.
- Students access attendance only via emailed session links. For improved security, session links MUST use short-lived JWT tokens (aud=attendance, sub=session_id, exp). Do not rely on HMAC-signed ad-hoc URLs.
- Because students do not log in, the system must validate eligibility server-side (program/stream membership, session status, duplicate attendance).

### Restrictions
- Cannot login to system
- Cannot view historical attendance
- Cannot access any system features beyond scanning QR code
- Cannot modify personal information

---

## Role Comparison Table

| Feature | Admin | Lecturer | Student |
|---------|-------|----------|---------|
| Login Required | ✅ Yes | ✅ Yes | ❌ No |
| Register Students | ✅ Yes | ❌ No | ❌ No |
| Self-register (Lecturer) | ❌ No | ✅ Yes | ❌ No |
| Create Sessions | ❌ No | ✅ Yes (own courses) | ❌ No |
| Mark Attendance | ❌ No | ❌ No | ✅ Yes |
| Generate Reports | ✅ All sessions | ✅ Own sessions | ❌ No |
| Manage Courses | ✅ Yes | ❌ No | ❌ No |
| Manage Programs | ✅ Yes | ❌ No | ❌ No |
| System Config | ✅ Yes | ❌ No | ❌ No |
| View All Data | ✅ Yes | ❌ No | ❌ No |

---

## Role Assignment Rules

1. **One Role Per User**
   - Each user account has exactly one role
   - Roles are mutually exclusive
   - Role determines which profile is created (LecturerProfile or StudentProfile)

2. **Profile Creation**
   - Admin: No additional profile
   - Lecturer: LecturerProfile created when lecturer self-registers (or requests activation); admins may only activate/manage lecturer accounts
   - Student: StudentProfile created automatically when admin registers the student

3. **Role Cannot Change**
   - Once assigned, roles should not be changed
   - To change role, create new user account
   - Maintains data integrity and audit trail

---

## Security Considerations

### Admin Security
- Strongest authentication requirements
- Activity logging for all admin actions
- Limited number of admin accounts
- Regular password rotation recommended

### Lecturer Security
- Standard authentication
- Session-based access control
- Activity logging for session creation and report generation
- Lecturers self-register or request activation; admin may activate and manage lecturer accounts but cannot create new lecturer accounts

### Student Security
- Time-limited or signed session links (recommended)
- Location-based validation
- QR code contains only student ID (no sensitive data)
- One-time attendance per session prevents replay attacks