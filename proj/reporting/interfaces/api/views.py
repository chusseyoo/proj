"""DRF view wrappers for reporting endpoints."""
import os
from dataclasses import asdict
from typing import Any

try:
    from rest_framework.views import APIView
    from rest_framework.response import Response
    from rest_framework import status
    from rest_framework.permissions import IsAuthenticated
except Exception:  # pragma: no cover
    APIView = object
    Response = dict
    status = type("S", (), {"HTTP_201_CREATED": 201, "HTTP_200_OK": 200})
    IsAuthenticated = object

from django.http import FileResponse

from reporting.interfaces.api.handlers.generate_report_handler import (
    GenerateReportHandler,
)
from reporting.interfaces.api.handlers.export_report_handler import (
    ExportReportHandler,
)
from reporting.interfaces.api.handlers.download_report_handler import (
    DownloadReportHandler,
)
from reporting.interfaces.api.permissions import (
    IsLecturerOrAdmin,
    IsSessionOwnerOrAdmin,
    IsReportOwnerOrAdmin,
    IsAdminUser,
)
from reporting.interfaces.api.serializers import (
    ExportReportRequestSerializer,
    ReportResponseSerializer,
    ExportResultSerializer,
    ReportListResponseSerializer,
)
from reporting.application.use_cases.view_report import ViewReportUseCase
from reporting.application.use_cases.list_reports import ListReportsUseCase
from reporting.domain.services.report_generator import ReportGenerator
from reporting.domain.services.report_access_policy import ReportAccessPolicy
from reporting.domain.exceptions import (
    SessionNotFoundError,
    ReportNotFoundError,
    UnauthorizedReportAccessError,
    ReportAlreadyExportedError,
)
from reporting.infrastructure.di import get_report_repository
from reporting.domain.services.attendance_aggregator import AttendanceAggregator


def _session_to_dict(session: Any) -> dict[str, Any]:
    """Map session model/object to response fields using best-effort attributes."""
    return {
        "session_id": getattr(session, "session_id", getattr(session, "id", None)),
        "course_name": getattr(getattr(session, "course", None), "name", None),
        "course_code": getattr(getattr(session, "course", None), "code", None),
        "program_name": getattr(getattr(session, "program", None), "name", None),
        "program_code": getattr(getattr(session, "program", None), "code", None),
        "stream_name": getattr(getattr(session, "stream", None), "name", None),
        "time_created": getattr(session, "time_created", None),
        "time_ended": getattr(session, "time_ended", None),
        "lecturer_name": getattr(getattr(getattr(session, "lecturer", None), "user", None), "get_full_name", lambda: None)(),
    }


class GenerateReportView(APIView):
    """POST /api/v1/sessions/{session_id}/report/ -> Generate new report."""

    permission_classes = [IsAuthenticated, IsSessionOwnerOrAdmin]

    def post(self, request, session_id: int):
        """Generate a new report for a session (201 Created).

        Permissions: Lecturer must own session or be admin.
        """
        try:
            handler = GenerateReportHandler()
            result = handler.handle(session_id, request.user)

            serializer = ReportResponseSerializer(result)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except SessionNotFoundError as e:
            return Response(
                {"code": "SESSION_NOT_FOUND", "message": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except UnauthorizedReportAccessError as e:
            return Response(
                {"code": "FORBIDDEN", "message": str(e)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception as e:  # pragma: no cover - safety
            return Response(
                {"code": "REPORT_GENERATION_FAILED", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ViewReportView(APIView):
    """GET /api/v1/reports/{report_id}/ -> View report details."""

    permission_classes = [IsAuthenticated, IsReportOwnerOrAdmin]

    def get(self, request, report_id: int):
        """Retrieve full report with statistics and students (200 OK)."""
        try:
            repo = get_report_repository()
            generator = ReportGenerator(AttendanceAggregator())
            access_policy = ReportAccessPolicy()
            use_case = ViewReportUseCase(repo, generator, access_policy)

            result = use_case.execute(report_id, request.user)

            serialized = ReportResponseSerializer(
                {
                    "report_id": result.report_id,
                    "session": _session_to_dict(result.session),
                    "statistics": asdict(result.statistics),
                    "students": [asdict(s) for s in result.students],
                    "generated_date": result.generated_date,
                    "generated_by": result.generated_by,
                    "export_status": result.export_status,
                }
            )
            return Response(serialized.data, status=status.HTTP_200_OK)
        except ReportNotFoundError as e:
            return Response(
                {"code": "REPORT_NOT_FOUND", "message": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except UnauthorizedReportAccessError as e:
            return Response(
                {"code": "FORBIDDEN", "message": str(e)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception as e:  # pragma: no cover - safety
            return Response(
                {"code": "REPORT_RETRIEVAL_FAILED", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExportReportView(APIView):
    """POST /api/v1/reports/{report_id}/export/ -> Export report to CSV/Excel."""

    permission_classes = [IsAuthenticated, IsReportOwnerOrAdmin]

    def post(self, request, report_id: int):
        """Export report to CSV or Excel (200 OK or 409 Conflict if re-export).

        Request body: {"file_type": "csv" or "excel"}
        """
        serializer = ExportReportRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "code": "INVALID_FILE_TYPE",
                    "message": "file_type must be 'csv' or 'excel'",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_type = serializer.validated_data["file_type"]

        try:
            handler = ExportReportHandler()
            result = handler.handle(report_id, file_type, request.user)

            export_serializer = ExportResultSerializer(result)
            return Response(export_serializer.data, status=status.HTTP_200_OK)
        except ReportNotFoundError as e:
            return Response(
                {"code": "REPORT_NOT_FOUND", "message": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ReportAlreadyExportedError as e:
            return Response(
                {"code": "REPORT_ALREADY_EXPORTED", "message": str(e)},
                status=status.HTTP_409_CONFLICT,
            )
        except UnauthorizedReportAccessError as e:
            return Response(
                {"code": "FORBIDDEN", "message": str(e)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception as e:  # pragma: no cover - safety
            return Response(
                {"code": "EXPORT_FAILED", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DownloadReportView(APIView):
    """GET /api/v1/reports/{report_id}/download/ -> Download exported file."""

    permission_classes = [IsAuthenticated, IsReportOwnerOrAdmin]

    def get(self, request, report_id: int):
        """Download exported report file (200 OK with binary content).

        Query params: ?file_type=csv|excel (optional, defaults to latest)
        """
        try:
            handler = DownloadReportHandler()
            result = handler.handle(report_id, request.user)

            file_path = result.file_path
            file_type = result.file_type or "csv"
            filename = result.filename or os.path.basename(file_path)

            # Open file stream for response
            try:
                file_stream = open(file_path, "rb")
            except FileNotFoundError as fnf:
                return Response(
                    {"code": "FILE_NOT_AVAILABLE", "message": str(fnf)},
                    status=status.HTTP_404_NOT_FOUND,
                )

            content_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                if file_type == "excel"
                else "text/csv"
            )

            return FileResponse(
                file_stream,
                content_type=content_type,
                as_attachment=True,
                filename=filename,
            )
        except ReportNotFoundError as e:
            return Response(
                {"code": "REPORT_NOT_FOUND", "message": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except UnauthorizedReportAccessError as e:
            return Response(
                {"code": "FORBIDDEN", "message": str(e)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception as e:  # pragma: no cover - safety
            return Response(
                {"code": "DOWNLOAD_FAILED", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ListReportsView(APIView):
    """GET /api/v1/reports/ -> List all reports (admin only)."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """List all reports with pagination (200 OK).

        Query params: ?page=1&page_size=10
        """
        try:
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("page_size", 10))

            use_case = ListReportsUseCase(get_report_repository())
            result = use_case.execute(
                requested_by=request.user,
                page=page,
                page_size=page_size,
            )

            response_payload = asdict(result)
            serializer = ReportListResponseSerializer(response_payload)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UnauthorizedReportAccessError as e:
            return Response(
                {"code": "FORBIDDEN", "message": str(e)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception as e:  # pragma: no cover - safety
            return Response(
                {"code": "LIST_FAILED", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

