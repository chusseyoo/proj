"""API exceptions package for academic_structure.

Re-exports the context-specific custom exception handler for simpler imports.
"""

from .custom_exception_handler import custom_exception_handler

__all__ = [
	"custom_exception_handler",
]
