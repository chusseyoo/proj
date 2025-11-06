"""API exceptions package for user_management.

Re-exports the context-specific custom exception handler for simpler imports.
"""

from .exception_handler import custom_exception_handler

__all__ = [
    "custom_exception_handler",
]
