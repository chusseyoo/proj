"""Report entity/aggregate scaffold.

Minimal dataclass representing a persisted report record. In the real
implementation this may map to a Django model; the dataclass here is for
in-memory representations used by the application layer.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from reporting.domain.exceptions import ReportingError


@dataclass
class Report:
    """Domain Report entity with basic behaviors.

    This dataclass is intentionally lightweight and stores the minimal set
    of fields needed by the application and infra layers. It exposes
    behaviours commonly needed by application use-cases (validation,
    export marking and simple (de)serialization).
    """

    id: Optional[int]
    session_id: int
    generated_by: int
    generated_date: Optional[str] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None

    def is_exported(self) -> bool:
        """Return True when report has been exported (has a file path)."""
        return bool(self.file_path)

    def mark_exported(self, file_path: str, file_type: str, generated_date: Optional[str] = None) -> "Report":
        """Mark this report as exported by setting file metadata.

        If generated_date is None, use current UTC ISO timestamp.
        Raises ReportingError for invalid inputs.
        Returns self for fluent usage.
        """
        if not file_path:
            raise ReportingError("file_path must be a non-empty string")
        if not file_type:
            raise ReportingError("file_type must be a non-empty string")

        self.file_path = file_path
        self.file_type = file_type
        if generated_date is None:
            # Use timezone-aware UTC timestamp
            self.generated_date = datetime.now(timezone.utc).isoformat()
        else:
            self.generated_date = generated_date
        return self

    def validate(self) -> None:
        """Validate entity invariants; raise ReportingError on failure."""
        if not isinstance(self.session_id, int) or self.session_id <= 0:
            raise ReportingError("session_id must be a positive integer")
        if not isinstance(self.generated_by, int) or self.generated_by <= 0:
            raise ReportingError("generated_by must be a positive integer")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entity to a plain dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "generated_by": self.generated_by,
            "generated_date": self.generated_date,
            "file_path": self.file_path,
            "file_type": self.file_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Report":
        """Create a Report from a plain mapping (e.g. DB row or dict).

        This performs minimal coercion only; use `validate()` explicitly
        if you want invariants checked.
        """
        return cls(
            id=data.get("id"),
            session_id=int(data["session_id"]),
            generated_by=int(data["generated_by"]),
            generated_date=data.get("generated_date"),
            file_path=data.get("file_path"),
            file_type=data.get("file_type"),
        )

    @classmethod
    def from_orm(cls, orm_obj: Any) -> "Report":
        """Create a domain Report from an ORM model instance.

        This helper assumes the ORM exposes attributes named to match the
        dataclass fields (id, session_id, generated_by, generated_date,
        file_path, file_type). It performs defensive attribute access.
        """
        return cls(
            id=getattr(orm_obj, "id", None),
            session_id=getattr(orm_obj, "session_id"),
            generated_by=getattr(orm_obj, "generated_by"),
            generated_date=getattr(orm_obj, "generated_date", None),
            file_path=getattr(orm_obj, "file_path", None),
            file_type=getattr(orm_obj, "file_type", None),
        )