"""Domain exceptions for reporting context."""


class ReportingError(Exception):
    """Base class for reporting domain errors."""
    pass


class UnauthorizedReportAccessError(ReportingError):
    """Raised when a user attempts to access or generate a report they don't have permission for."""
    pass


class ReportAlreadyExportedError(ReportingError):
    """Raised when attempting to export a report that has already been exported."""
    pass


class FileGenerationError(ReportingError):
    """Raised when there's an error generating an export file."""
    pass


class ReportNotFoundError(ReportingError):
    """Raised when a requested report doesn't exist."""
    pass


class SessionNotFoundError(ReportingError):
    """Raised when a session referenced in report generation doesn't exist."""
    pass
