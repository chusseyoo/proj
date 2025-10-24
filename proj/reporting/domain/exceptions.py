"""Domain exceptions for reporting context."""


class ReportingError(Exception):
    """Base class for reporting domain errors."""
    pass


class UnauthorizedReportAccessError(ReportingError):
    pass


class ReportAlreadyExportedError(ReportingError):
    pass


class FileGenerationError(ReportingError):
    pass
