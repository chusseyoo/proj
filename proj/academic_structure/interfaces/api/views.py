"""REST API Views for Academic Structure.

This module provides ViewSets for Program, Stream, and Course resources.
Follows endpoint specifications from api_guide.md.

Base path: /api/academic-structure/v1/
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.paginator import Paginator

from ...application.use_cases.program import (
    CreateProgramUseCase,
    GetProgramUseCase,
    GetProgramByCodeUseCase,
    ListProgramsUseCase,
    UpdateProgramUseCase,
    DeleteProgramUseCase
)
from ...application.use_cases.stream import (
    CreateStreamUseCase,
    GetStreamUseCase,
    ListStreamsByProgramUseCase,
    UpdateStreamUseCase,
    DeleteStreamUseCase
)
from ...application.use_cases.course import (
    CreateCourseUseCase,
    GetCourseUseCase,
    GetCourseByCodeUseCase,
    ListCoursesUseCase,
    ListUnassignedCoursesUseCase,
    UpdateCourseUseCase,
    DeleteCourseUseCase,
    AssignLecturerUseCase,
    UnassignLecturerUseCase
)
from ...infrastructure.repositories import (
    ProgramRepository,
    StreamRepository,
    CourseRepository
)
from ...domain.exceptions import (
    ProgramNotFoundError,
    ProgramCodeAlreadyExistsError,
    ProgramCannotBeDeletedError,
    StreamNotFoundError,
    StreamAlreadyExistsError,
    StreamCannotBeDeletedError,
    StreamNotAllowedError,
    CourseNotFoundError,
    CourseCodeAlreadyExistsError,
    CourseCannotBeDeletedError,
    LecturerNotFoundError,
    LecturerInactiveError,
    ValidationError
)
from .serializers import (
    ProgramSerializer,
    StreamSerializer,
    CourseSerializer,
    AssignLecturerSerializer,
    ErrorSerializer
)
from .permissions import IsAdminUser, IsLecturerOrAdmin


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_error_response(exception, status_code):
    """Create standardized error response.
    
    Args:
        exception: The exception that was raised
        status_code: HTTP status code for the response
        
    Returns:
        Response object with error details
    """
    error_data = {
        'error': {
            'code': exception.__class__.__name__,
            'message': str(exception),
            'details': getattr(exception, 'details', None)
        }
    }
    
    return Response(error_data, status=status_code)


def create_paginated_response(items, page, page_size, total_count):
    """Create standardized paginated response.
    
    Args:
        items: List of items for current page
        page: Current page number (1-based)
        page_size: Number of items per page
        total_count: Total number of items across all pages
        
    Returns:
        dict with pagination metadata and results
    """
    total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0
    
    return {
        'results': items,
        'total_count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_previous': page > 1
    }


# ============================================================================
# PROGRAM VIEWSET
# ============================================================================

class ProgramViewSet(viewsets.ViewSet):
    """ViewSet for Program resource.
    
    Endpoints:
    - GET    /programs/              - List programs (filterable, paginated)
    - POST   /programs/              - Create program (admin only)
    - GET    /programs/{id}/         - Retrieve program by ID
    - GET    /programs/by-code/{code}/ - Retrieve program by code
    - PATCH  /programs/{id}/         - Update program (admin only)
    - DELETE /programs/{id}/         - Delete program (admin only)
    """
    
    def get_permissions(self):
        """Instantiate and return the list of permissions."""
        if self.action in ['list', 'retrieve', 'by_code']:
            # Lecturers and Admins can read
            permission_classes = [IsLecturerOrAdmin]
        else:
            # Only Admins can write
            permission_classes = [IsAdminUser]
        
        return [permission() for permission in permission_classes]
    
    def list(self, request):
        """GET /programs/ - List programs with optional filters and pagination.
        
        Query parameters:
        - department_name (str): Filter by department
        - has_streams (bool): Filter by has_streams flag
        - search (str): Search in program_name and program_code
        - page (int): Page number (default: 1)
        - page_size (int): Items per page (default: 20, max: 100)
        - ordering (str): Sort field (name, code, -name, -code)
        """
        try:
            # Initialize repository and use case
            program_repo = ProgramRepository()
            use_case = ListProgramsUseCase(program_repo)
            
            # Extract query parameters
            department_name = request.query_params.get('department_name')
            has_streams = request.query_params.get('has_streams')
            search = request.query_params.get('search')
            
            # Parse has_streams boolean
            if has_streams is not None:
                has_streams = has_streams.lower() == 'true'
            
            # Execute use case
            program_dtos = use_case.execute(
                department_name=department_name,
                has_streams=has_streams
            )
            
            # Apply search filter if provided
            if search:
                search_lower = search.lower()
                program_dtos = [
                    dto for dto in program_dtos
                    if search_lower in dto.program_name.lower() or
                       search_lower in dto.program_code.lower()
                ]
            
            # Apply ordering
            ordering = request.query_params.get('ordering', 'program_code')
            reverse = ordering.startswith('-')
            order_field = ordering.lstrip('-')
            
            if order_field in ['name', 'program_name']:
                program_dtos.sort(key=lambda x: x.program_name, reverse=reverse)
            elif order_field in ['code', 'program_code']:
                program_dtos.sort(key=lambda x: x.program_code, reverse=reverse)
            
            # Pagination
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 20)), 100)
            
            paginator = Paginator(program_dtos, page_size)
            page_obj = paginator.get_page(page)
            
            # Serialize results
            serializer = ProgramSerializer(page_obj.object_list, many=True)
            
            # Create paginated response
            response_data = create_paginated_response(
                serializer.data,
                page,
                page_size,
                paginator.count
            )
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def create(self, request):
        """POST /programs/ - Create a new program (admin only).
        
        Request body:
        {
          "program_name": "BSc Computer Science",
          "program_code": "BCS",
          "department_name": "Computer Science",
          "has_streams": true
        }
        """
        serializer = ProgramSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Initialize repository and use case
            program_repo = ProgramRepository()
            use_case = CreateProgramUseCase(program_repo)
            
            # Execute use case
            program_dto = use_case.execute(serializer.validated_data)
            
            # Serialize response
            response_serializer = ProgramSerializer(program_dto)
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except ProgramCodeAlreadyExistsError as e:
            return create_error_response(e, status.HTTP_409_CONFLICT)
        except ValidationError as e:
            return create_error_response(e, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def retrieve(self, request, pk=None):
        """GET /programs/{id}/ - Retrieve program by ID."""
        try:
            # Initialize repository and use case
            program_repo = ProgramRepository()
            use_case = GetProgramUseCase(program_repo)
            
            # Execute use case
            program_dto = use_case.execute(int(pk))
            
            # Serialize response
            serializer = ProgramSerializer(program_dto)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ProgramNotFoundError as e:
            return create_error_response(e, status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='by-code/(?P<program_code>[^/.]+)')
    def by_code(self, request, program_code=None):
        """GET /programs/by-code/{program_code}/ - Retrieve program by code (case-insensitive)."""
        try:
            # Initialize repository and use case
            program_repo = ProgramRepository()
            use_case = GetProgramByCodeUseCase(program_repo)
            
            # Execute use case
            program_dto = use_case.execute(program_code)
            
            # Serialize response
            serializer = ProgramSerializer(program_dto)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ProgramNotFoundError as e:
            return create_error_response(e, status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def partial_update(self, request, pk=None):
        """PATCH /programs/{id}/ - Update program (admin only).
        
        Mutable fields: program_name, department_name, has_streams
        Immutable: program_code (will raise 400 if attempted)
        """
        serializer = ProgramSerializer(data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Initialize repository and use case
            program_repo = ProgramRepository()
            use_case = UpdateProgramUseCase(program_repo)
            
            # Execute use case
            program_dto = use_case.execute(int(pk), serializer.validated_data)
            
            # Serialize response
            response_serializer = ProgramSerializer(program_dto)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except ProgramNotFoundError as e:
            return create_error_response(e, status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return create_error_response(e, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def destroy(self, request, pk=None):
        """DELETE /programs/{id}/ - Safe delete program (admin only).
        
        Will fail if:
        - Students are enrolled in program
        - Courses exist for program
        """
        try:
            # Initialize repository and use case
            program_repo = ProgramRepository()
            use_case = DeleteProgramUseCase(program_repo)
            
            # Execute use case
            use_case.execute(int(pk))
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except ProgramNotFoundError as e:
            return create_error_response(e, status.HTTP_404_NOT_FOUND)
        except ProgramCannotBeDeletedError as e:
            return create_error_response(e, status.HTTP_409_CONFLICT)
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# STREAM VIEWSET
# ============================================================================

class StreamViewSet(viewsets.ViewSet):
    """ViewSet for Stream resource.
    
    Endpoints:
    - GET    /programs/{program_id}/streams/  - List streams for program
    - POST   /programs/{program_id}/streams/  - Create stream (admin only)
    - GET    /streams/{id}/                   - Retrieve stream by ID
    - PATCH  /streams/{id}/                   - Update stream (admin only)
    - DELETE /streams/{id}/                   - Delete stream (admin only)
    """
    
    def get_permissions(self):
        """Instantiate and return the list of permissions."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsLecturerOrAdmin]
        else:
            permission_classes = [IsAdminUser]
        
        return [permission() for permission in permission_classes]
    
    def list(self, request, program_pk=None):
        """GET /programs/{program_id}/streams/ - List streams for program.
        
        Query parameters:
        - year_of_study (int): Filter by year (1-4)
        - ordering (str): Sort field (year_of_study, stream_name)
        """
        try:
            # Initialize repositories and use case
            program_repo = ProgramRepository()
            stream_repo = StreamRepository()
            use_case = ListStreamsByProgramUseCase(stream_repo, program_repo)
            
            # Extract query parameters
            year_of_study = request.query_params.get('year_of_study')
            if year_of_study:
                year_of_study = int(year_of_study)
            
            # Execute use case
            stream_dtos = use_case.execute(
                program_id=int(program_pk),
                year_of_study=year_of_study,
                include_program_code=True
            )
            
            # Apply ordering
            ordering = request.query_params.get('ordering', 'year_of_study')
            reverse = ordering.startswith('-')
            order_field = ordering.lstrip('-')
            
            if order_field == 'year_of_study':
                stream_dtos.sort(key=lambda x: x.year_of_study, reverse=reverse)
            elif order_field == 'stream_name':
                stream_dtos.sort(key=lambda x: x.stream_name, reverse=reverse)
            
            # Serialize results
            serializer = StreamSerializer(stream_dtos, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ProgramNotFoundError as e:
            return create_error_response(e, status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def create(self, request, program_pk=None):
        """POST /programs/{program_id}/streams/ - Create stream (admin only).
        
        Request body:
        {
          "stream_name": "Stream A",
          "year_of_study": 2
        }
        """
        # Add program_id to data
        data = request.data.copy()
        data['program_id'] = int(program_pk)
        
        serializer = StreamSerializer(data=data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Initialize repositories and use case
            program_repo = ProgramRepository()
            stream_repo = StreamRepository()
            use_case = CreateStreamUseCase(stream_repo, program_repo)
            
            # Execute use case
            stream_dto = use_case.execute(serializer.validated_data)
            
            # Serialize response
            response_serializer = StreamSerializer(stream_dto)
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except ProgramNotFoundError as e:
            return create_error_response(e, status.HTTP_404_NOT_FOUND)
        except StreamAlreadyExistsError as e:
            return create_error_response(e, status.HTTP_409_CONFLICT)
        except StreamNotAllowedError as e:
            return create_error_response(e, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except ValidationError as e:
            return create_error_response(e, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def retrieve(self, request, pk=None):
        """GET /streams/{id}/ - Retrieve stream by ID."""
        try:
            # Initialize repositories and use case
            program_repo = ProgramRepository()
            stream_repo = StreamRepository()
            use_case = GetStreamUseCase(stream_repo, program_repo)
            
            # Execute use case
            stream_dto = use_case.execute(
                stream_id=int(pk),
                include_program_code=True
            )
            
            # Serialize response
            serializer = StreamSerializer(stream_dto)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except StreamNotFoundError as e:
            return create_error_response(e, status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def partial_update(self, request, pk=None):
        """PATCH /streams/{id}/ - Update stream (admin only).
        
        Mutable fields: stream_name, year_of_study
        Immutable: program_id (will raise 400 if attempted)
        """
        serializer = StreamSerializer(data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Initialize repositories and use case
            stream_repo = StreamRepository()
            use_case = UpdateStreamUseCase(stream_repo)
            
            # Execute use case
            stream_dto = use_case.execute(
                stream_id=int(pk),
                updates=serializer.validated_data
            )
            
            # Serialize response
            response_serializer = StreamSerializer(stream_dto)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except StreamNotFoundError as e:
            return create_error_response(e, status.HTTP_404_NOT_FOUND)
        except StreamAlreadyExistsError as e:
            return create_error_response(e, status.HTTP_409_CONFLICT)
        except ValidationError as e:
            return create_error_response(e, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def destroy(self, request, pk=None):
        """DELETE /streams/{id}/ - Safe delete stream (admin only).
        
        Will fail if students are assigned to stream.
        """
        try:
            # Initialize repository and use case
            stream_repo = StreamRepository()
            use_case = DeleteStreamUseCase(stream_repo)
            
            # Execute use case
            use_case.execute(int(pk))
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except StreamNotFoundError as e:
            return create_error_response(e, status.HTTP_404_NOT_FOUND)
        except StreamCannotBeDeletedError as e:
            return create_error_response(e, status.HTTP_409_CONFLICT)
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# COURSE VIEWSET
# ============================================================================

class CourseViewSet(viewsets.ViewSet):
    """ViewSet for Course resource.
    
    Endpoints:
    - GET    /courses/                      - List courses (filterable, paginated)
    - POST   /courses/                      - Create course (admin only)
    - GET    /courses/{id}/                 - Retrieve course by ID
    - GET    /courses/by-code/{code}/       - Retrieve course by code
    - PATCH  /courses/{id}/                 - Update course (admin only)
    - DELETE /courses/{id}/                 - Delete course (admin only)
    - POST   /courses/{id}/assign-lecturer/ - Assign lecturer (admin only)
    - POST   /courses/{id}/unassign-lecturer/ - Unassign lecturer (admin only)
    """
    
    def get_permissions(self):
        """Instantiate and return the list of permissions."""
        if self.action in ['list', 'retrieve', 'by_code']:
            permission_classes = [IsLecturerOrAdmin]
        else:
            permission_classes = [IsAdminUser]
        
        return [permission() for permission in permission_classes]
    
    def list(self, request):
        """GET /courses/ - List courses with optional filters and pagination.
        
        Query parameters:
        - program_id (int): Filter by program
        - lecturer_id (int): Filter by lecturer (null for unassigned)
        - department_name (str): Filter by department
        - q (str): Search in course_code and course_name
        - page (int): Page number (default: 1)
        - page_size (int): Items per page (default: 20, max: 100)
        - ordering (str): Sort field (course_code, -course_code)
        """
        try:
            # Initialize repositories and use case
            program_repo = ProgramRepository()
            course_repo = CourseRepository()
            use_case = ListCoursesUseCase(course_repo, program_repo)
            
            # Extract query parameters
            program_id = request.query_params.get('program_id')
            lecturer_id = request.query_params.get('lecturer_id')
            
            if program_id:
                program_id = int(program_id)
            if lecturer_id:
                lecturer_id = int(lecturer_id)
            
            # Execute use case
            course_dtos = use_case.execute(
                program_id=program_id,
                lecturer_id=lecturer_id,
                include_program_code=True,
                include_lecturer_name=True
            )
            
            # Apply department filter
            department_name = request.query_params.get('department_name')
            if department_name:
                course_dtos = [
                    dto for dto in course_dtos
                    if dto.department_name.lower() == department_name.lower()
                ]
            
            # Apply search filter
            q = request.query_params.get('q')
            if q:
                q_lower = q.lower()
                course_dtos = [
                    dto for dto in course_dtos
                    if q_lower in dto.course_code.lower() or
                       q_lower in dto.course_name.lower()
                ]
            
            # Apply ordering
            ordering = request.query_params.get('ordering', 'course_code')
            reverse = ordering.startswith('-')
            order_field = ordering.lstrip('-')
            
            if order_field == 'course_code':
                course_dtos.sort(key=lambda x: x.course_code, reverse=reverse)
            
            # Pagination
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 20)), 100)
            
            paginator = Paginator(course_dtos, page_size)
            page_obj = paginator.get_page(page)
            
            # Serialize results
            serializer = CourseSerializer(page_obj.object_list, many=True)
            
            # Create paginated response
            response_data = create_paginated_response(
                serializer.data,
                page,
                page_size,
                paginator.count
            )
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def create(self, request):
        """POST /courses/ - Create a new course (admin only).
        
        Request body:
        {
          "course_code": "CS201",
          "course_name": "Data Structures",
          "program_id": 1,
          "department_name": "Computer Science",
          "lecturer_id": 17  // optional
        }
        """
        serializer = CourseSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Initialize repositories and use case
            program_repo = ProgramRepository()
            course_repo = CourseRepository()
            use_case = CreateCourseUseCase(course_repo, program_repo)
            
            # Execute use case
            course_dto = use_case.execute(serializer.validated_data)
            
            # Serialize response
            response_serializer = CourseSerializer(course_dto)
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except CourseCodeAlreadyExistsError as e:
            return create_error_response(e, status.HTTP_409_CONFLICT)
        except (ProgramNotFoundError, LecturerNotFoundError) as e:
            return create_error_response(e, status.HTTP_404_NOT_FOUND)
        except LecturerInactiveError as e:
            return create_error_response(e, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except ValidationError as e:
            return create_error_response(e, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def retrieve(self, request, pk=None):
        """GET /courses/{id}/ - Retrieve course by ID."""
        try:
            # Initialize repositories and use case
            program_repo = ProgramRepository()
            course_repo = CourseRepository()
            use_case = GetCourseUseCase(course_repo, program_repo)
            
            # Execute use case
            course_dto = use_case.execute(
                course_id=int(pk),
                include_program_code=True,
                include_lecturer_name=True
            )
            
            # Serialize response
            serializer = CourseSerializer(course_dto)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except CourseNotFoundError as e:
            return create_error_response(e, status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='by-code/(?P<course_code>[^/.]+)')
    def by_code(self, request, course_code=None):
        """GET /courses/by-code/{course_code}/ - Retrieve course by code (case-insensitive)."""
        try:
            # Initialize repositories and use case
            program_repo = ProgramRepository()
            course_repo = CourseRepository()
            use_case = GetCourseByCodeUseCase(course_repo, program_repo)
            
            # Execute use case
            course_dto = use_case.execute(
                course_code=course_code,
                include_program_code=True,
                include_lecturer_name=True
            )
            
            # Serialize response
            serializer = CourseSerializer(course_dto)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except CourseNotFoundError as e:
            return create_error_response(e, status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def partial_update(self, request, pk=None):
        """PATCH /courses/{id}/ - Update course (admin only).
        
        Mutable fields: course_name, department_name, lecturer_id
        Immutable: course_code, program_id (will raise 400 if attempted)
        """
        serializer = CourseSerializer(data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Initialize repositories and use case
            course_repo = CourseRepository()
            use_case = UpdateCourseUseCase(course_repo)
            
            # Execute use case
            course_dto = use_case.execute(
                course_id=int(pk),
                updates=serializer.validated_data,
                include_program_code=True,
                include_lecturer_name=True
            )
            
            # Serialize response
            response_serializer = CourseSerializer(course_dto)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except CourseNotFoundError as e:
            return create_error_response(e, status.HTTP_404_NOT_FOUND)
        except LecturerNotFoundError as e:
            return create_error_response(e, status.HTTP_404_NOT_FOUND)
        except LecturerInactiveError as e:
            return create_error_response(e, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except ValidationError as e:
            return create_error_response(e, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def destroy(self, request, pk=None):
        """DELETE /courses/{id}/ - Safe delete course (admin only).
        
        Will fail if sessions exist for this course.
        """
        try:
            # Initialize repository and use case
            course_repo = CourseRepository()
            use_case = DeleteCourseUseCase(course_repo)
            
            # Execute use case
            use_case.execute(int(pk))
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except CourseNotFoundError as e:
            return create_error_response(e, status.HTTP_404_NOT_FOUND)
        except CourseCannotBeDeletedError as e:
            return create_error_response(e, status.HTTP_409_CONFLICT)
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='assign-lecturer')
    def assign_lecturer(self, request, pk=None):
        """POST /courses/{id}/assign-lecturer/ - Assign lecturer to course (admin only).
        
        Request body:
        {
          "lecturer_id": 17
        }
        """
        serializer = AssignLecturerSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Initialize repository and use case
            course_repo = CourseRepository()
            use_case = AssignLecturerUseCase(course_repo)
            
            # Execute use case
            course_dto = use_case.execute(
                course_id=int(pk),
                lecturer_id=serializer.validated_data['lecturer_id'],
                include_program_code=True
            )
            
            # Serialize response
            response_serializer = CourseSerializer(course_dto)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except CourseNotFoundError as e:
            return create_error_response(e, status.HTTP_404_NOT_FOUND)
        except LecturerNotFoundError as e:
            return create_error_response(e, status.HTTP_404_NOT_FOUND)
        except LecturerInactiveError as e:
            return create_error_response(e, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='unassign-lecturer')
    def unassign_lecturer(self, request, pk=None):
        """POST /courses/{id}/unassign-lecturer/ - Remove lecturer from course (admin only)."""
        try:
            # Initialize repository and use case
            course_repo = CourseRepository()
            use_case = UnassignLecturerUseCase(course_repo)
            
            # Execute use case
            course_dto = use_case.execute(
                course_id=int(pk),
                include_program_code=True
            )
            
            # Serialize response
            response_serializer = CourseSerializer(course_dto)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except CourseNotFoundError as e:
            return create_error_response(e, status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)
