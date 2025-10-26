"""Lightweight DI (construction helpers) for reporting infrastructure.

This module provides small factory functions to obtain the default
infrastructure collaborators used by the application layer. Callers (views,
tests) can import these helpers and optionally override the returned
instances for testing.
"""
from typing import Any


def get_report_repository() -> Any:
    """Return the default ORM-backed report repository instance.

    Imports are performed inside the function to avoid importing Django at
    module import time. Callers should expect that constructing the
    repository may require Django to be available.
    """
    from reporting.infrastructure.repositories.orm_repository import OrmReportRepository

    return OrmReportRepository()


def get_exporter_factory() -> Any:
    """Return the exporter factory instance (CSV, etc.)."""
    from reporting.infrastructure.exporters.factory import ExporterFactory

    return ExporterFactory()


def get_storage_adapter() -> Any:
    """Return a storage adapter configured with project MEDIA_ROOT.

    This does a lazy import of Django settings; if Django is not available
    the adapter will be constructed with base_dir=None which most adapters
    handle by using a sensible default or raising on use.
    """
    try:
        from django.conf import settings  # type: ignore
        base = getattr(settings, "MEDIA_ROOT", None)
    except Exception:
        base = None

    from reporting.infrastructure.storage.adapter import FilesystemStorageAdapter

    return FilesystemStorageAdapter(base_dir=base)
