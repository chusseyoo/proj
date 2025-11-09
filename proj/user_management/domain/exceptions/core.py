"""
Domain exceptions for User Management context.

These exceptions represent business rule violations and error conditions
in the domain layer.
"""


class UserManagementException(Exception):
    """Base exception for user management domain."""
    pass


# User-related exceptions
class UserNotFoundError(UserManagementException):
    """Raised when a user cannot be found."""
    def __init__(self, identifier: str = None):
        if identifier:
            super().__init__(f"User not found: {identifier}")
        else:
            super().__init__("User not found")


class EmailAlreadyExistsError(UserManagementException):
    """Raised when attempting to register with an existing email."""
    def __init__(self, email: str):
        super().__init__(f"Email address already exists: {email}")
        self.email = email


class UserInactiveError(UserManagementException):
    """Raised when attempting operations on an inactive user."""
    def __init__(self, user_id: int = None):
        if user_id:
            super().__init__(f"User {user_id} is inactive")
        else:
            super().__init__("User account is inactive")


# Student-related exceptions
class StudentNotFoundError(UserManagementException):
    """Raised when a student profile cannot be found."""
    def __init__(self, identifier: str = None):
        if identifier:
            super().__init__(f"Student not found: {identifier}")
        else:
            super().__init__("Student profile not found")


class StudentIdAlreadyExistsError(UserManagementException):
    """Raised when attempting to register with an existing student ID."""
    def __init__(self, student_id: str):
        super().__init__(f"Student ID already exists: {student_id}")
        self.student_id = student_id


class InvalidStudentIdFormatError(UserManagementException):
    """Raised when student ID doesn't match required format."""
    def __init__(self, student_id: str):
        super().__init__(
            f"Invalid student ID format: {student_id}. Expected format: ABC/123456"
        )
        self.student_id = student_id


class StudentCannotHavePasswordError(UserManagementException):
    """Raised when attempting to set password for a student."""
    def __init__(self):
        super().__init__("Students cannot have passwords. Use passwordless authentication.")


class StudentCannotLoginError(UserManagementException):
    """Raised when student attempts password-based login."""
    def __init__(self):
        super().__init__(
            "Students cannot log in with password. Please use the email link provided."
        )


# Lecturer-related exceptions
class LecturerNotFoundError(UserManagementException):
    """Raised when a lecturer profile cannot be found."""
    def __init__(self, identifier: str = None):
        if identifier:
            super().__init__(f"Lecturer not found: {identifier}")
        else:
            super().__init__("Lecturer profile not found")


# Stream/Program-related exceptions
class ProgramNotFoundError(UserManagementException):
    """Raised when a program doesn't exist."""
    def __init__(self, program_id: int):
        super().__init__(f"Program not found: {program_id}")
        self.program_id = program_id


class StreamRequiredError(UserManagementException):
    """Raised when stream is required but not provided."""
    def __init__(self, program_name: str = None):
        if program_name:
            super().__init__(f"Stream is required for program: {program_name}")
        else:
            super().__init__("Stream is required for this program")


class StreamNotAllowedError(UserManagementException):
    """Raised when stream is provided but program doesn't have streams."""
    def __init__(self, program_name: str = None):
        if program_name:
            super().__init__(f"Program {program_name} does not have streams")
        else:
            super().__init__("This program does not have streams")


class StreamNotInProgramError(UserManagementException):
    """Raised when stream doesn't belong to the specified program."""
    def __init__(self, stream_name: str = None, program_name: str = None):
        if stream_name and program_name:
            super().__init__(f"Stream {stream_name} does not belong to program {program_name}")
        else:
            super().__init__("Stream does not belong to this program")


class InvalidYearError(UserManagementException):
    """Raised when year of study is out of valid range."""
    def __init__(self, year: int):
        super().__init__(f"Invalid year of study: {year}. Must be between 1 and 4.")
        self.year = year


class ProgramCodeMismatchError(UserManagementException):
    """Raised when student ID program code doesn't match enrolled program code."""
    def __init__(self, student_id_code: str, program_code: str):
        super().__init__(
            f"Student ID program code '{student_id_code}' does not match "
            f"enrolled program code '{program_code}'"
        )
        self.student_id_code = student_id_code
        self.program_code = program_code


class InvalidDepartmentNameError(UserManagementException):
    """Raised when department name is invalid."""
    def __init__(self, reason: str = "Invalid department name"):
        super().__init__(reason)


# Authentication exceptions
class InvalidCredentialsError(UserManagementException):
    """Raised when login credentials are invalid."""
    def __init__(self):
        super().__init__("Invalid credentials")


class InvalidPasswordError(UserManagementException):
    """Raised when password verification fails."""
    def __init__(self):
        super().__init__("Invalid password")


class WeakPasswordError(UserManagementException):
    """Raised when password doesn't meet strength requirements."""
    def __init__(self, reason: str = None):
        if reason:
            super().__init__(f"Password is too weak: {reason}")
        else:
            super().__init__("Password does not meet strength requirements")
        self.reason = reason


# Token exceptions
class InvalidTokenError(UserManagementException):
    """Raised when JWT token is invalid."""
    def __init__(self, reason: str = "Token is invalid"):
        super().__init__(reason)


class ExpiredTokenError(UserManagementException):
    """Raised when JWT token has expired."""
    def __init__(self):
        super().__init__("Token has expired")


class InvalidTokenTypeError(UserManagementException):
    """Raised when token type doesn't match expected type."""
    def __init__(self, expected: str, actual: str):
        super().__init__(f"Expected {expected} token, got {actual}")
        self.expected = expected
        self.actual = actual


class TokenAlreadyUsedError(UserManagementException):
    """Raised when attempting to use a one-time token that was already used."""
    def __init__(self):
        super().__init__("This token has already been used")


# Authorization exceptions
class UnauthorizedError(UserManagementException):
    """Raised when user lacks permission for an action."""
    def __init__(self, action: str = None):
        if action:
            super().__init__(f"You do not have permission to {action}")
        else:
            super().__init__("You do not have permission to perform this action")
