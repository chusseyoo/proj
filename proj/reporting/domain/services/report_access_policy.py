"""Domain-level policy helpers for report actions."""
from reporting.domain.exceptions import UnauthorizedReportAccessError


class ReportAccessPolicy:
    @staticmethod
    def ensure_can_generate(session, requested_by) -> None:
        role = None
        user_id = None
        if isinstance(requested_by, dict):
            role = requested_by.get("role")
            user_id = requested_by.get("id")
        else:
            role = getattr(requested_by, "role", None)
            user_id = getattr(requested_by, "id", None)

        if role == "admin":
            return

        owner_id = session.get("owner_id") if isinstance(session, dict) else getattr(session, "owner_id", None)
        if role == "lecturer" and owner_id == user_id:
            return

        raise UnauthorizedReportAccessError("not allowed to generate this report")

    @staticmethod
    def ensure_can_export(requested_by) -> None:
        role = None
        if isinstance(requested_by, dict):
            role = requested_by.get("role")
        else:
            role = getattr(requested_by, "role", None)

        if role in {"admin", "lecturer"}:
            return

        raise UnauthorizedReportAccessError("not allowed to export this report")
