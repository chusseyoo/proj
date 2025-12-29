"""Duplicate Attendance Policy - Business rule for re-scans.

This policy defines how the system handles duplicate attendance attempts.
Enforcement happens at two levels:
1. Domain: Raise exception if duplicate is detected
2. Database: UNIQUE constraint on (student_id, session_id) prevents duplicates
"""


class DuplicateAttendancePolicy:
    """Enforces the rule: One attendance record per student per session.
    
    Business Rule:
    - A student can only mark attendance once per session
    - If re-scan attempt is made, return error with instructive message
    - Database UNIQUE constraint prevents duplicates at storage layer
    
    Responsibility:
    - Domain/repository checks if attendance already exists
    - Returns DuplicateAttendanceError before attempting database insert
    - Exception message explains that attendance is already recorded
    """
    
    @staticmethod
    def check_duplicate(existing_attendance: dict | None) -> None:
        """Check if attendance already exists for this student-session pair.
        
        This method is called by repository before creating new attendance.
        
        Args:
            existing_attendance: Attendance record if it exists, None otherwise
        
        Raises:
            DuplicateAttendanceError: If attendance already exists
        
        Example:
            # In repository layer:
            existing = self.get_by_student_and_session(student_id, session_id)
            DuplicateAttendancePolicy.check_duplicate(existing)  # Raises if exists
            # If no exception, safe to create new record
        """
        from ..exceptions import DuplicateAttendanceError
        
        if existing_attendance is not None:
            raise DuplicateAttendanceError(
                "Attendance already recorded for this student in this session. "
                "Re-scanning is not allowed. Contact lecturer if this is an error."
            )
    
    @staticmethod
    def get_policy_description() -> str:
        """Describe the duplicate attendance policy for documentation."""
        return (
            "Duplicate Attendance Policy:\n"
            "- One attendance record per student per session\n"
            "- Enforced by: (1) Domain check, (2) Database UNIQUE constraint\n"
            "- Re-scan attempts return error\n"
            "- Error message guides user to contact lecturer if mistaken\n"
            "- Database constraint prevents race conditions in high-concurrency scenarios"
        )
