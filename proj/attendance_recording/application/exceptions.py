"""Application-level exceptions for attendance recording."""


class ApplicationError(Exception):
	"""Base application-layer exception."""


class RequestValidationError(ApplicationError):
	"""Raised when incoming request data is invalid."""

	def __init__(self, message: str, details: dict | None = None):
		super().__init__(message)
		self.details = details or {}


class ResourceNotFoundError(ApplicationError):
	"""Raised when required resources cannot be located."""


class ConflictError(ApplicationError):
	"""Raised when a business conflict occurs (e.g., duplicates)."""


__all__ = [
	"ApplicationError",
	"RequestValidationError",
	"ResourceNotFoundError",
	"ConflictError",
]
