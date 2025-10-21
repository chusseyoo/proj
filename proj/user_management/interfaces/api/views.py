"""
DRF API Views for User Management.

Handles HTTP requests, validates via serializers, calls use cases,
returns HTTP responses per api_guide.md.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .serializers import (
    LoginSerializer,
    LoginResponseSerializer,
    RefreshTokenSerializer,
    RefreshTokenResponseSerializer,
    RegisterLecturerSerializer,
    RegisterStudentSerializer,
    RegisterAdminSerializer,
    RegistrationResponseSerializer,
    UserSerializer,
    UpdateUserSerializer,
    StudentProfileSerializer,
    UpdateStudentProfileSerializer,
    LecturerProfileSerializer,
    UpdateLecturerProfileSerializer,
)
from .permissions import IsAdmin, IsOwnerOrAdmin, IsAuthenticated
from .authentication import JWTAuthentication

from ...application.use_cases import (
    LoginUseCase,
    RefreshAccessTokenUseCase,
    RegisterLecturerUseCase,
    RegisterStudentUseCase,
    RegisterAdminUseCase,
    GetUserByIdUseCase,
    UpdateUserUseCase,
    DeactivateUserUseCase,
    GetStudentProfileByUserIdUseCase,
    UpdateStudentProfileUseCase,
    GetLecturerProfileByUserIdUseCase,
    UpdateLecturerProfileUseCase,
)

# Service/repo imports for use case instantiation
from ...application.services import (
    AuthenticationService,
    PasswordService,
    UserService,
    ProfileService,
    RegistrationService,
)
from ...infrastructure.repositories import (
    UserRepository,
    StudentProfileRepository,
    LecturerProfileRepository,
)


# ============================================================================
# AUTH VIEWS
# ============================================================================

class LoginView(APIView):
    """
    POST /api/users/login
    
    Authenticate user (Admin/Lecturer) and return JWT tokens.
    Public endpoint.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Instantiate use case
        auth_service = self._get_auth_service()
        use_case = LoginUseCase(auth=auth_service)
        
        # Execute
        result = use_case.handle(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        
        # Return response
        return Response(result, status=status.HTTP_200_OK)
    
    def _get_auth_service(self):
        return AuthenticationService(
            user_repository=UserRepository(),
            password_service=PasswordService(),
            student_repository=StudentProfileRepository(),
            refresh_store=None,
        )


class RefreshTokenView(APIView):
    """
    POST /api/users/refresh
    
    Refresh access token using refresh token.
    Public endpoint (token validation handled in use case).
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Instantiate use case
        auth_service = self._get_auth_service()
        use_case = RefreshAccessTokenUseCase(auth=auth_service)
        
        # Execute
        result = use_case.handle(
            refresh_token=serializer.validated_data['refresh_token']
        )
        
        return Response(result, status=status.HTTP_200_OK)
    
    def _get_auth_service(self):
        return AuthenticationService(
            user_repository=UserRepository(),
            password_service=PasswordService(),
            student_repository=StudentProfileRepository(),
            refresh_store=None,
        )


# ============================================================================
# REGISTRATION VIEWS
# ============================================================================

class RegisterLecturerView(APIView):
    """
    POST /api/users/register/lecturer
    
    Self-registration for lecturers.
    Public endpoint, auto-activated.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegisterLecturerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Instantiate use case
        registration_service = self._get_registration_service()
        use_case = RegisterLecturerUseCase(registration=registration_service)
        
        # Execute
        result = use_case.handle(lecturer_data=serializer.validated_data)
        
        # Format response
        response_data = {
            'user_id': result['user'].user_id,
            'email': str(result['user'].email),
            'role': result['user'].role.value,
            'is_active': result['user'].is_active,
            'access_token': result['access_token'],
            'refresh_token': result['refresh_token'],
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    def _get_registration_service(self):
        return RegistrationService(
            user_repository=UserRepository(),
            student_repository=StudentProfileRepository(),
            lecturer_repository=LecturerProfileRepository(),
            password_service=PasswordService(),
            authentication_service=AuthenticationService(
                user_repository=UserRepository(),
                password_service=PasswordService(),
                student_repository=StudentProfileRepository(),
                refresh_store=None,
            ),
        )


class RegisterStudentView(APIView):
    """
    POST /api/users/register/student
    
    Register student (Admin only).
    No password, qr_code_data auto-set.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]
    
    def post(self, request):
        serializer = RegisterStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Instantiate use case
        registration_service = self._get_registration_service()
        use_case = RegisterStudentUseCase(registration=registration_service)
        
        # Execute (pass admin_user from request.user)
        result = use_case.handle(
            student_data=serializer.validated_data,
            admin_user=request.user
        )
        
        # Format response
        response_data = {
            'user_id': result['user'].user_id,
            'student_profile_id': result['student_profile'].student_profile_id,
            'student_id': str(result['student_profile'].student_id),
            'email': str(result['user'].email),
            'role': result['user'].role.value,
            'is_active': result['user'].is_active,
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    def _get_registration_service(self):
        return RegistrationService(
            user_repository=UserRepository(),
            student_repository=StudentProfileRepository(),
            lecturer_repository=LecturerProfileRepository(),
            password_service=PasswordService(),
            authentication_service=AuthenticationService(
                user_repository=UserRepository(),
                password_service=PasswordService(),
                student_repository=StudentProfileRepository(),
                refresh_store=None,
            ),
        )


class RegisterAdminView(APIView):
    """
    POST /api/users/register/admin
    
    Register admin (Admin only).
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]
    
    def post(self, request):
        serializer = RegisterAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Instantiate use case
        registration_service = self._get_registration_service()
        use_case = RegisterAdminUseCase(registration=registration_service)
        
        # Execute
        result = use_case.handle(
            admin_data=serializer.validated_data,
            creator_admin=request.user
        )
        
        # Format response
        response_data = {
            'user_id': result['user'].user_id,
            'email': str(result['user'].email),
            'role': result['user'].role.value,
            'is_active': result['user'].is_active,
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    def _get_registration_service(self):
        return RegistrationService(
            user_repository=UserRepository(),
            student_repository=StudentProfileRepository(),
            lecturer_repository=LecturerProfileRepository(),
            password_service=PasswordService(),
            authentication_service=AuthenticationService(
                user_repository=UserRepository(),
                password_service=PasswordService(),
                student_repository=StudentProfileRepository(),
                refresh_store=None,
            ),
        )


# ============================================================================
# USER VIEWS
# ============================================================================

class UserDetailView(APIView):
    """
    GET /api/users/{user_id}
    PUT /api/users/{user_id}
    DELETE /api/users/{user_id}
    
    Get, update, or deactivate user.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsOwnerOrAdmin]
    
    def get(self, request, user_id):
        """Get user by ID."""
        use_case = GetUserByIdUseCase(users=self._get_user_service())
        result = use_case.handle(user_id=user_id, include_profile=True)
        
        # Serialize user
        user_data = {
            'user_id': result['user'].user_id,
            'first_name': result['user'].first_name,
            'last_name': result['user'].last_name,
            'email': str(result['user'].email),
            'role': result['user'].role.value,
            'is_active': result['user'].is_active,
            'date_joined': result['user'].date_joined,
        }
        
        return Response(user_data, status=status.HTTP_200_OK)
    
    def put(self, request, user_id):
        """Update user."""
        serializer = UpdateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        use_case = UpdateUserUseCase(users=self._get_user_service())
        updated_user = use_case.handle(
            actor=request.user,
            user_id=user_id,
            update_data=serializer.validated_data
        )
        
        # Serialize updated user
        user_data = {
            'user_id': updated_user.user_id,
            'first_name': updated_user.first_name,
            'last_name': updated_user.last_name,
            'email': str(updated_user.email),
            'role': updated_user.role.value,
            'is_active': updated_user.is_active,
            'date_joined': updated_user.date_joined,
        }
        
        return Response(user_data, status=status.HTTP_200_OK)
    
    def delete(self, request, user_id):
        """Deactivate user (soft delete)."""
        use_case = DeactivateUserUseCase(users=self._get_user_service())
        deactivated_user = use_case.handle(actor=request.user, user_id=user_id)
        
        return Response(
            {'message': 'User deactivated successfully'},
            status=status.HTTP_200_OK
        )
    
    def _get_user_service(self):
        return UserService(
            user_repository=UserRepository(),
            student_repository=StudentProfileRepository(),
            lecturer_repository=LecturerProfileRepository(),
        )


# ============================================================================
# PROFILE VIEWS
# ============================================================================

class StudentProfileView(APIView):
    """
    GET /api/users/{user_id}/student-profile
    PUT /api/users/{user_id}/student-profile
    
    Get or update student profile.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsOwnerOrAdmin]
    
    def get(self, request, user_id):
        """Get student profile by user_id."""
        use_case = GetStudentProfileByUserIdUseCase(profiles=self._get_profile_service())
        result = use_case.handle(user_id=user_id)
        
        profile = result['student_profile']
        profile_data = {
            'student_profile_id': profile.student_profile_id,
            'student_id': str(profile.student_id),
            'user_id': profile.user_id,
            'program_id': profile.program_id,
            'stream_id': profile.stream_id,
            'year_of_study': profile.year_of_study,
            'qr_code_data': profile.qr_code_data,
        }
        
        return Response(profile_data, status=status.HTTP_200_OK)
    
    def put(self, request, user_id):
        """Update student profile."""
        serializer = UpdateStudentProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get student_profile_id from user_id first
        get_use_case = GetStudentProfileByUserIdUseCase(profiles=self._get_profile_service())
        get_result = get_use_case.handle(user_id=user_id)
        student_profile_id = get_result['student_profile'].student_profile_id
        
        # Update profile
        update_use_case = UpdateStudentProfileUseCase(profiles=self._get_profile_service())
        result = update_use_case.handle(
            student_profile_id=student_profile_id,
            update_data=serializer.validated_data
        )
        
        profile = result['student_profile']
        profile_data = {
            'student_profile_id': profile.student_profile_id,
            'student_id': str(profile.student_id),
            'user_id': profile.user_id,
            'program_id': profile.program_id,
            'stream_id': profile.stream_id,
            'year_of_study': profile.year_of_study,
            'qr_code_data': profile.qr_code_data,
        }
        
        return Response(profile_data, status=status.HTTP_200_OK)
    
    def _get_profile_service(self):
        return ProfileService(
            student_repository=StudentProfileRepository(),
            lecturer_repository=LecturerProfileRepository(),
        )


class LecturerProfileView(APIView):
    """
    GET /api/users/{user_id}/lecturer-profile
    PUT /api/users/{user_id}/lecturer-profile
    
    Get or update lecturer profile.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsOwnerOrAdmin]
    
    def get(self, request, user_id):
        """Get lecturer profile by user_id."""
        use_case = GetLecturerProfileByUserIdUseCase(profiles=self._get_profile_service())
        result = use_case.handle(user_id=user_id)
        
        profile = result['lecturer_profile']
        profile_data = {
            'lecturer_id': profile.lecturer_profile_id,
            'user_id': profile.user_id,
            'department_name': profile.department_name,
        }
        
        return Response(profile_data, status=status.HTTP_200_OK)
    
    def put(self, request, user_id):
        """Update lecturer profile."""
        serializer = UpdateLecturerProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get lecturer_profile_id from user_id first
        get_use_case = GetLecturerProfileByUserIdUseCase(profiles=self._get_profile_service())
        get_result = get_use_case.handle(user_id=user_id)
        lecturer_id = get_result['lecturer_profile'].lecturer_profile_id
        
        # Update profile
        update_use_case = UpdateLecturerProfileUseCase(profiles=self._get_profile_service())
        result = update_use_case.handle(
            lecturer_id=lecturer_id,
            update_data=serializer.validated_data
        )
        
        profile = result['lecturer_profile']
        profile_data = {
            'lecturer_id': profile.lecturer_profile_id,
            'user_id': profile.user_id,
            'department_name': profile.department_name,
        }
        
        return Response(profile_data, status=status.HTTP_200_OK)
    
    def _get_profile_service(self):
        return ProfileService(
            student_repository=StudentProfileRepository(),
            lecturer_repository=LecturerProfileRepository(),
        )
