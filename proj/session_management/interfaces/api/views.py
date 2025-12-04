"""REST API views for Session Management."""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from math import ceil

from .serializers import (
    CreateSessionRequestSerializer,
    SessionResponseSerializer,
    PaginatedSessionResponseSerializer,
    SessionFilterSerializer,
)
from .permissions import IsLecturer, IsSessionOwner
from .error_handlers import handle_use_case_exception, format_error_response
from ...application.use_cases.create_session import CreateSessionUseCase
from ...application.use_cases.list_sessions import ListMySessionsUseCase
from ...application.use_cases.get_session import GetSessionUseCase
from ...application.use_cases.end_session import EndSessionUseCase
from ...application.factory import build_inmemory_container
from ...domain.services.session_rules import SessionService


def get_lecturer_id(request):
    """Extract lecturer ID from authenticated user."""
    if hasattr(request.user, 'lecturer_profile'):
        return request.user.lecturer_profile.lecturer_id
    return None


# Build a singleton in-memory container so state persists across requests in tests
_CONTAINER = build_inmemory_container()

def build_use_cases():
    """Return pre-built use cases from the singleton container."""
    return {
        'create': _CONTAINER['create'],
        'list': _CONTAINER['list'],
        'get': _CONTAINER['get'],
        'end': _CONTAINER['end'],
    }


class SessionListCreateView(APIView):
    """
    List sessions or create a new session.
    
    GET /api/session-management/v1/sessions
    POST /api/session-management/v1/sessions
    """
    permission_classes = [IsAuthenticated, IsLecturer]
    
    def post(self, request):
        """Create a new session."""
        # Validate request data
        serializer = CreateSessionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                format_error_response("ValidationError", serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get lecturer ID from auth
        lecturer_id = get_lecturer_id(request)
        if not lecturer_id:
            return Response(
                format_error_response("AuthorizationError", "User is not a lecturer"),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Execute use case
        try:
            use_cases = build_use_cases()
            result = use_cases['create'].execute(lecturer_id, serializer.validated_data)
            
            # Serialize response
            response_serializer = SessionResponseSerializer(result)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            # Domain exceptions handled by error_handlers
            from ...domain.exceptions.core import DomainException
            from ...application.exceptions import CommandValidationError
            
            if isinstance(e, (DomainException, CommandValidationError)):
                from .error_handlers import get_error_code, DOMAIN_EXCEPTION_STATUS_MAP
                error_code = get_error_code(e)
                http_status = DOMAIN_EXCEPTION_STATUS_MAP.get(error_code, status.HTTP_400_BAD_REQUEST)
                return Response(
                    format_error_response(error_code, str(e)),
                    status=http_status
                )
            raise
    
    def get(self, request):
        """List sessions with filters and pagination."""
        # Validate query parameters
        filter_serializer = SessionFilterSerializer(data=request.query_params)
        if not filter_serializer.is_valid():
            return Response(
                format_error_response("ValidationError", filter_serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get lecturer ID from auth
        lecturer_id = get_lecturer_id(request)
        if not lecturer_id:
            return Response(
                format_error_response("AuthorizationError", "User is not a lecturer"),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Build filters
        filters = filter_serializer.validated_data
        page = filters.pop('page', 1)
        page_size = filters.pop('page_size', 20)
        
        # Add lecturer filter (lecturers only see their own sessions)
        filters['lecturer_id'] = lecturer_id
        
        # Execute use case
        try:
            use_cases = build_use_cases()
            # The ListMySessionsUseCase already returns a paginated dict
            result = use_cases['list'].execute(
                auth_lecturer_id=lecturer_id,
                program_id=filters.get('program_id'),
                course_id=filters.get('course_id'),
                stream_id=filters.get('stream_id'),
                start=filters.get('from_time'),
                end=filters.get('to_time'),
                page=page,
                page_size=page_size,
            )
            response_serializer = PaginatedSessionResponseSerializer(result)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            from ...domain.exceptions.core import DomainException
            from ...application.exceptions import CommandValidationError
            
            if isinstance(e, (DomainException, CommandValidationError)):
                from .error_handlers import get_error_code, DOMAIN_EXCEPTION_STATUS_MAP
                error_code = get_error_code(e)
                http_status = DOMAIN_EXCEPTION_STATUS_MAP.get(error_code, status.HTTP_400_BAD_REQUEST)
                return Response(
                    format_error_response(error_code, str(e)),
                    status=http_status
                )
            raise


class SessionDetailView(APIView):
    """
    Retrieve a specific session.
    
    GET /api/session-management/v1/sessions/{session_id}
    """
    permission_classes = [IsAuthenticated, IsLecturer]
    
    def get(self, request, session_id):
        """Get session details."""
        # Get lecturer ID from auth
        lecturer_id = get_lecturer_id(request)
        if not lecturer_id:
            return Response(
                format_error_response("AuthorizationError", "User is not a lecturer"),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Execute use case
        try:
            use_cases = build_use_cases()
            result = use_cases['get'].execute(session_id, lecturer_id)
            
            # Serialize response
            response_serializer = SessionResponseSerializer(result)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            from ...domain.exceptions.core import DomainException
            from ...application.exceptions import CommandValidationError
            
            if isinstance(e, (DomainException, CommandValidationError)):
                from .error_handlers import get_error_code, DOMAIN_EXCEPTION_STATUS_MAP
                error_code = get_error_code(e)
                http_status = DOMAIN_EXCEPTION_STATUS_MAP.get(error_code, status.HTTP_400_BAD_REQUEST)
                return Response(
                    format_error_response(error_code, str(e)),
                    status=http_status
                )
            raise


class SessionEndNowView(APIView):
    """
    End a session immediately.
    
    POST /api/session-management/v1/sessions/{session_id}/end-now
    """
    permission_classes = [IsAuthenticated, IsLecturer]
    
    def post(self, request, session_id):
        """End session now."""
        # Get lecturer ID from auth
        lecturer_id = get_lecturer_id(request)
        if not lecturer_id:
            return Response(
                format_error_response("AuthorizationError", "User is not a lecturer"),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Execute use case
        try:
            use_cases = build_use_cases()
            result = use_cases['end'].execute(session_id, lecturer_id)
            
            # Serialize response
            response_serializer = SessionResponseSerializer(result)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            from ...domain.exceptions.core import DomainException
            from ...application.exceptions import CommandValidationError
            
            if isinstance(e, (DomainException, CommandValidationError)):
                from .error_handlers import get_error_code, DOMAIN_EXCEPTION_STATUS_MAP
                error_code = get_error_code(e)
                http_status = DOMAIN_EXCEPTION_STATUS_MAP.get(error_code, status.HTTP_400_BAD_REQUEST)
                return Response(
                    format_error_response(error_code, str(e)),
                    status=http_status
                )
            raise
