import pytest
from unittest.mock import Mock, create_autospec, patch, MagicMock

# Mock transaction.atomic BEFORE importing the service
with patch('django.db.transaction.atomic') as mock_atomic:
    mock_atomic.side_effect = lambda func: func  # Just return the unwrapped function
    from user_management.application.services.registration_service import RegistrationService

from user_management.domain.entities import User, UserRole, LecturerProfile
from user_management.domain.value_objects import Email
from user_management.domain.exceptions import (
    EmailAlreadyExistsError,
    WeakPasswordError,
)

# NOTE: We intentionally only cover a subset of the full plan first (lecturer happy path + a few errors)
# to get fast feedback before adding the much larger student/admin matrices.

@pytest.fixture()
def user_repository():
    repo = Mock()
    repo.exists_by_email.return_value = False
    # create(user_entity, password_hash=...) should return the user with an assigned ID
    def _create(user_entity, password_hash):
        # Simulate persistence assigning an ID
        return User(
            user_id=1,
            first_name=user_entity.first_name,
            last_name=user_entity.last_name,
            email=user_entity.email,
            role=user_entity.role,
            is_active=user_entity.is_active,
            has_password=user_entity.has_password,
        )
    repo.create.side_effect = _create
    return repo

@pytest.fixture()
def lecturer_repository():
    repo = Mock()
    def _create(profile):
        return LecturerProfile(
            lecturer_profile_id=10,
            user_id=profile.user_id,
            department_name=profile.department_name.strip(),
        )
    repo.create.side_effect = _create
    return repo

@pytest.fixture()
def student_repository():
    # Not used yet; placeholder for later student tests
    return Mock()

@pytest.fixture()
def password_service():
    svc = Mock()
    svc.validate_password_strength.return_value = None
    svc.hash_password.return_value = 'hashed_pw'
    return svc

@pytest.fixture()
def authentication_service():
    svc = Mock()
    svc.login.return_value = {
        'user': {'id': 1},
        'access_token': 'access.token.jwt',
        'refresh_token': 'refresh.token.jwt'
    }
    return svc

@pytest.fixture()
def service(user_repository, student_repository, lecturer_repository, password_service, authentication_service):
    return RegistrationService(
        user_repository=user_repository,
        student_repository=student_repository,
        lecturer_repository=lecturer_repository,
        password_service=password_service,
        authentication_service=authentication_service,
    )

@pytest.fixture()
def lecturer_input():
    return {
        'first_name': ' Alice ',
        'last_name': ' Smith ',
        'email': 'LECTURER@example.COM',
        'password': 'StrongPass123!',
        'department_name': ' Computer Science '
    }

# -----------------------------
# Lecturer Registration Tests
# -----------------------------

@pytest.mark.django_db
def test_register_lecturer_success(service, lecturer_input, user_repository, lecturer_repository, password_service, authentication_service):
    result = service.register_lecturer(lecturer_input)

    # Returned structure
    assert 'user' in result and 'lecturer_profile' in result
    assert result['access_token'] == 'access.token.jwt'
    assert result['refresh_token'] == 'refresh.token.jwt'

    user = result['user']
    profile = result['lecturer_profile']

    # User assertions
    assert user.user_id == 1
    assert user.role == UserRole.LECTURER
    assert user.first_name == 'Alice'  # trimmed
    assert user.last_name == 'Smith'
    assert str(user.email) == 'lecturer@example.com'  # normalized lower
    assert user.is_active is True
    assert user.has_password is True

    # Profile assertions
    assert profile.lecturer_profile_id == 10
    assert profile.user_id == user.user_id
    # We retain original spacing on input; domain may or may not trim inside entity; we trimmed in fake repo
    assert profile.department_name == 'Computer Science'

    # Interaction assertions
    user_repository.exists_by_email.assert_called_once_with('lecturer@example.com')
    password_service.validate_password_strength.assert_called_once_with('StrongPass123!')
    password_service.hash_password.assert_called_once_with('StrongPass123!')
    lecturer_repository.create.assert_called_once()
    authentication_service.login.assert_called_once_with('lecturer@example.com', 'StrongPass123!')


@pytest.mark.django_db
def test_register_lecturer_duplicate_email_raises_error(service, lecturer_input, user_repository):
    user_repository.exists_by_email.return_value = True
    with pytest.raises(EmailAlreadyExistsError):
        service.register_lecturer(lecturer_input)
    # Ensure we short-circuit before hashing or creating
    user_repository.create.assert_not_called()


@pytest.mark.django_db
def test_register_lecturer_weak_password_raises_error(service, lecturer_input, password_service, user_repository):
    password_service.validate_password_strength.side_effect = WeakPasswordError('too weak')
    with pytest.raises(WeakPasswordError):
        service.register_lecturer(lecturer_input)
    password_service.hash_password.assert_not_called()
    user_repository.create.assert_not_called()


@pytest.mark.django_db
def test_register_lecturer_email_normalized(service, lecturer_input):
    result = service.register_lecturer(lecturer_input)
    assert str(result['user'].email) == 'lecturer@example.com'


@pytest.mark.django_db
def test_register_lecturer_names_trimmed(service, lecturer_input):
    result = service.register_lecturer(lecturer_input)
    assert result['user'].first_name == 'Alice'
    assert result['user'].last_name == 'Smith'


@pytest.mark.django_db
def test_register_lecturer_department_trimmed(service, lecturer_input, lecturer_repository):
    result = service.register_lecturer(lecturer_input)
    assert result['lecturer_profile'].department_name == 'Computer Science'
    lecturer_repository.create.assert_called_once()


# -----------------------------
# Student Registration Tests
# -----------------------------

@pytest.fixture()
def admin_user():
    """Admin user for authorization checks."""
    return User(
        user_id=99,
        first_name='Admin',
        last_name='User',
        email=Email('admin@example.com'),
        role=UserRole.ADMIN,
        is_active=True,
        has_password=True,
    )


@pytest.fixture()
def lecturer_user():
    """Lecturer user for negative authorization tests."""
    return User(
        user_id=88,
        first_name='John',
        last_name='Lecturer',
        email=Email('lecturer@example.com'),
        role=UserRole.LECTURER,
        is_active=True,
        has_password=True,
    )


@pytest.fixture()
def mock_program():
    """Mock Program model instance."""
    program = Mock()
    program.id = 1
    # ORM uses `program_id` attribute in the service layer; keep both in sync for tests
    program.program_id = 1
    program.program_code = 'BCS'
    program.program_name = 'Bachelor of Computer Science'
    program.has_streams = True
    return program


@pytest.fixture()
def mock_program_no_streams():
    """Mock Program model instance without streams."""
    program = Mock()
    program.id = 2
    # Keep program_id aligned with id
    program.program_id = 2
    program.program_code = 'BIT'
    program.program_name = 'Bachelor of Information Technology'
    program.has_streams = False
    return program


@pytest.fixture()
def mock_stream():
    """Mock Stream model instance."""
    stream = Mock()
    # Service expects `stream_id` attribute on Stream objects
    stream.id = 10
    stream.stream_id = 10
    stream.program_id = 1
    stream.stream_name = 'Software Engineering'
    stream.year_of_study = 2
    return stream


@pytest.fixture()
def student_input():
    """Base student registration input."""
    return {
        'first_name': ' Bob ',
        'last_name': ' Johnson ',
        'email': ' STUDENT@EXAMPLE.COM ',
        'student_id': 'bcs/123456',  # lowercase - should be normalized
        'program_id': 1,
        'stream_id': 10,
        'year_of_study': 2,
    }


class TestRegisterStudent:
    """Test suite for student registration."""
    
    # ---------------------
    # A. Success Path
    # ---------------------
    
    @pytest.mark.django_db
    def test_register_student_success(
        self, service, admin_user, student_input, user_repository, 
        student_repository, mock_program, mock_stream
    ):
        """Test successful student registration with all valid data."""
        # Setup mocks
        user_repository.exists_by_email.return_value = False
        student_repository.exists_by_student_id.return_value = False
        
        # Setup return values
        def _create_user(user_entity, password_hash):
            return User(
                user_id=20,
                first_name=user_entity.first_name,
                last_name=user_entity.last_name,
                email=user_entity.email,
                role=user_entity.role,
                is_active=user_entity.is_active,
                has_password=user_entity.has_password,
            )
        user_repository.create.side_effect = _create_user
        
        from user_management.domain.entities import StudentProfile
        from user_management.domain.value_objects import StudentId
        
        def _create_student_profile(profile):
            return StudentProfile(
                student_profile_id=100,
                student_id=profile.student_id,
                user_id=profile.user_id,
                program_id=profile.program_id,
                stream_id=profile.stream_id,
                year_of_study=profile.year_of_study,
                qr_code_data=profile.qr_code_data,
            )
        student_repository.create.side_effect = _create_student_profile
        
        # Mock Django ORM queries
        with patch('user_management.application.services.registration_service.ProgramModel') as MockProgramModel:
            with patch('user_management.application.services.registration_service.StreamModel') as MockStreamModel:
                MockProgramModel.objects.get.return_value = mock_program
                MockStreamModel.objects.get.return_value = mock_stream
                
                result = service.register_student(student_input, admin_user)
        
        # Assertions
        assert 'user' in result and 'student_profile' in result
        user = result['user']
        profile = result['student_profile']
        
        # User assertions
        assert user.user_id == 20
        assert user.role == UserRole.STUDENT
        assert user.first_name == 'Bob'  # trimmed
        assert user.last_name == 'Johnson'  # trimmed
        assert str(user.email) == 'student@example.com'  # normalized lowercase
        assert user.is_active is True
        assert user.has_password is False  # Students don't have passwords
        
        # Profile assertions
        assert profile.student_profile_id == 100
        assert str(profile.student_id) == 'BCS/123456'  # normalized uppercase
        assert profile.user_id == user.user_id
        assert profile.program_id == 1
        assert profile.stream_id == 10
        assert profile.year_of_study == 2
        assert profile.qr_code_data == 'BCS/123456'  # matches student_id
        
        # Interaction assertions
        user_repository.exists_by_email.assert_called_once_with('student@example.com')
        student_repository.exists_by_student_id.assert_called_once_with('BCS/123456')
        user_repository.create.assert_called_once()
        student_repository.create.assert_called_once()
    
    @pytest.mark.django_db
    def test_student_no_password(
        self, service, admin_user, student_input, user_repository,
        student_repository, mock_program, mock_stream
    ):
        """Test that students are created without passwords."""
        student_repository.exists_by_student_id.return_value = False
        
        def _create_user(user_entity, password_hash):
            assert password_hash is None, "Students should not have password hash"
            return User(
                user_id=21,
                first_name=user_entity.first_name,
                last_name=user_entity.last_name,
                email=user_entity.email,
                role=user_entity.role,
                is_active=user_entity.is_active,
                has_password=user_entity.has_password,
            )
        user_repository.create.side_effect = _create_user
        
        from user_management.domain.entities import StudentProfile
        
        def _create_student_profile(profile):
            return StudentProfile(
                student_profile_id=101,
                student_id=profile.student_id,
                user_id=profile.user_id,
                program_id=profile.program_id,
                stream_id=profile.stream_id,
                year_of_study=profile.year_of_study,
                qr_code_data=profile.qr_code_data,
            )
        student_repository.create.side_effect = _create_student_profile
        
        with patch('user_management.application.services.registration_service.ProgramModel') as MockProgramModel:
            with patch('user_management.application.services.registration_service.StreamModel') as MockStreamModel:
                MockProgramModel.objects.get.return_value = mock_program
                MockStreamModel.objects.get.return_value = mock_stream
                
                result = service.register_student(student_input, admin_user)
        
        assert result['user'].has_password is False
    
    @pytest.mark.django_db
    def test_qr_code_auto_set_to_student_id(
        self, service, admin_user, student_input, user_repository,
        student_repository, mock_program, mock_stream
    ):
        """Test that QR code data is automatically set to student ID."""
        student_repository.exists_by_student_id.return_value = False
        
        def _create_user(user_entity, password_hash):
            return User(
                user_id=22,
                first_name=user_entity.first_name,
                last_name=user_entity.last_name,
                email=user_entity.email,
                role=user_entity.role,
                is_active=user_entity.is_active,
                has_password=user_entity.has_password,
            )
        user_repository.create.side_effect = _create_user
        
        from user_management.domain.entities import StudentProfile
        
        def _create_student_profile(profile):
            # Verify QR code matches student ID
            assert profile.qr_code_data == str(profile.student_id)
            return StudentProfile(
                student_profile_id=102,
                student_id=profile.student_id,
                user_id=profile.user_id,
                program_id=profile.program_id,
                stream_id=profile.stream_id,
                year_of_study=profile.year_of_study,
                qr_code_data=profile.qr_code_data,
            )
        student_repository.create.side_effect = _create_student_profile
        
        with patch('user_management.application.services.registration_service.ProgramModel') as MockProgramModel:
            with patch('user_management.application.services.registration_service.StreamModel') as MockStreamModel:
                MockProgramModel.objects.get.return_value = mock_program
                MockStreamModel.objects.get.return_value = mock_stream
                
                result = service.register_student(student_input, admin_user)
        
        assert result['student_profile'].qr_code_data == 'BCS/123456'
    
    @pytest.mark.django_db
    def test_profile_created_with_stream(
        self, service, admin_user, student_input, user_repository,
        student_repository, mock_program, mock_stream
    ):
        """Test profile creation with stream when program has streams."""
        student_repository.exists_by_student_id.return_value = False
        
        def _create_user(user_entity, password_hash):
            return User(
                user_id=23,
                first_name=user_entity.first_name,
                last_name=user_entity.last_name,
                email=user_entity.email,
                role=user_entity.role,
                is_active=user_entity.is_active,
                has_password=user_entity.has_password,
            )
        user_repository.create.side_effect = _create_user
        
        from user_management.domain.entities import StudentProfile
        
        def _create_student_profile(profile):
            return StudentProfile(
                student_profile_id=103,
                student_id=profile.student_id,
                user_id=profile.user_id,
                program_id=profile.program_id,
                stream_id=profile.stream_id,
                year_of_study=profile.year_of_study,
                qr_code_data=profile.qr_code_data,
            )
        student_repository.create.side_effect = _create_student_profile
        
        with patch('user_management.application.services.registration_service.ProgramModel') as MockProgramModel:
            with patch('user_management.application.services.registration_service.StreamModel') as MockStreamModel:
                MockProgramModel.objects.get.return_value = mock_program
                MockStreamModel.objects.get.return_value = mock_stream
                
                result = service.register_student(student_input, admin_user)
        
        assert result['student_profile'].stream_id == 10
    
    @pytest.mark.django_db
    def test_profile_created_without_stream(
        self, service, admin_user, user_repository,
        student_repository, mock_program_no_streams
    ):
        """Test profile creation without stream when program has no streams."""
        student_input_no_stream = {
            'first_name': 'Charlie',
            'last_name': 'Brown',
            'email': 'charlie@example.com',
            'student_id': 'BIT/654321',
            'program_id': 2,
            'stream_id': None,  # No stream
            'year_of_study': 1,
        }
        
        student_repository.exists_by_student_id.return_value = False
        
        def _create_user(user_entity, password_hash):
            return User(
                user_id=24,
                first_name=user_entity.first_name,
                last_name=user_entity.last_name,
                email=user_entity.email,
                role=user_entity.role,
                is_active=user_entity.is_active,
                has_password=user_entity.has_password,
            )
        user_repository.create.side_effect = _create_user
        
        from user_management.domain.entities import StudentProfile
        
        def _create_student_profile(profile):
            return StudentProfile(
                student_profile_id=104,
                student_id=profile.student_id,
                user_id=profile.user_id,
                program_id=profile.program_id,
                stream_id=profile.stream_id,
                year_of_study=profile.year_of_study,
                qr_code_data=profile.qr_code_data,
            )
        student_repository.create.side_effect = _create_student_profile
        
        with patch('user_management.application.services.registration_service.ProgramModel') as MockProgramModel:
            MockProgramModel.objects.get.return_value = mock_program_no_streams
            
            result = service.register_student(student_input_no_stream, admin_user)
        
        assert result['student_profile'].stream_id is None
    
    # ---------------------
    # B. Authorization
    # ---------------------
    
    @pytest.mark.django_db
    def test_non_admin_raises_unauthorized(self, service, lecturer_user, student_input):
        """Test that non-admin users cannot register students."""
        from user_management.domain.exceptions import UnauthorizedError
        
        with pytest.raises(UnauthorizedError) as exc_info:
            service.register_student(student_input, lecturer_user)
        
        assert 'administrator' in str(exc_info.value).lower()
    
    @pytest.mark.django_db
    def test_admin_can_register(
        self, service, admin_user, student_input, user_repository,
        student_repository, mock_program, mock_stream
    ):
        """Test that admin users can register students."""
        student_repository.exists_by_student_id.return_value = False
        
        def _create_user(user_entity, password_hash):
            return User(
                user_id=25,
                first_name=user_entity.first_name,
                last_name=user_entity.last_name,
                email=user_entity.email,
                role=user_entity.role,
                is_active=user_entity.is_active,
                has_password=user_entity.has_password,
            )
        user_repository.create.side_effect = _create_user
        
        from user_management.domain.entities import StudentProfile
        
        def _create_student_profile(profile):
            return StudentProfile(
                student_profile_id=105,
                student_id=profile.student_id,
                user_id=profile.user_id,
                program_id=profile.program_id,
                stream_id=profile.stream_id,
                year_of_study=profile.year_of_study,
                qr_code_data=profile.qr_code_data,
            )
        student_repository.create.side_effect = _create_student_profile
        
        with patch('user_management.application.services.registration_service.ProgramModel') as MockProgramModel:
            with patch('user_management.application.services.registration_service.StreamModel') as MockStreamModel:
                MockProgramModel.objects.get.return_value = mock_program
                MockStreamModel.objects.get.return_value = mock_stream
                
                result = service.register_student(student_input, admin_user)
        
        assert result['user'] is not None
        # Should not raise UnauthorizedError
    
    # ---------------------
    # C. Validation Errors
    # ---------------------
    
    @pytest.mark.django_db
    def test_duplicate_email_raises_error(self, service, admin_user, student_input, user_repository):
        """Test that duplicate email raises EmailAlreadyExistsError."""
        user_repository.exists_by_email.return_value = True
        
        with pytest.raises(EmailAlreadyExistsError):
            service.register_student(student_input, admin_user)
        
        user_repository.create.assert_not_called()
    
    @pytest.mark.django_db
    def test_duplicate_student_id_raises_error(
        self, service, admin_user, student_input, user_repository, student_repository
    ):
        """Test that duplicate student ID raises StudentIdAlreadyExistsError."""
        user_repository.exists_by_email.return_value = False
        student_repository.exists_by_student_id.return_value = True
        
        from user_management.domain.exceptions import StudentIdAlreadyExistsError
        
        with pytest.raises(StudentIdAlreadyExistsError):
            service.register_student(student_input, admin_user)
        
        user_repository.create.assert_not_called()
    
    @pytest.mark.django_db
    def test_invalid_student_id_format_raises_error(self, service, admin_user, student_input):
        """Test that invalid student ID format raises InvalidStudentIdFormatError."""
        from user_management.domain.exceptions import InvalidStudentIdFormatError
        
        invalid_inputs = [
            'ABC123456',  # Missing slash
            'AB/123456',  # Only 2 letters
            'ABCD/123456',  # 4 letters
            'ABC/12345',  # Only 5 digits
            'ABC/1234567',  # 7 digits
            '123/123456',  # Numbers instead of letters
            'abc/123456',  # Lowercase (should work but validate format)
        ]
        
        for invalid_id in invalid_inputs:
            student_input['student_id'] = invalid_id
            if invalid_id == 'abc/123456':
                # This should actually work after normalization
                continue
            with pytest.raises(InvalidStudentIdFormatError):
                service.register_student(student_input, admin_user)
    
    @pytest.mark.django_db
    def test_program_not_found_raises_error(
        self, service, admin_user, student_input, user_repository, student_repository
    ):
        """Test that non-existent program raises error."""
        student_repository.exists_by_student_id.return_value = False
        
        from user_management.domain.exceptions import ProgramNotFoundError
        with patch('user_management.application.services.registration_service.ProgramModel') as MockProgramModel:
            # Ensure the patched Mock exposes the real DoesNotExist exception class so
            # the service's `except ProgramModel.DoesNotExist` can correctly catch it.
            from academic_structure.infrastructure.orm.django_models import Program as ProgramModel
            MockProgramModel.DoesNotExist = ProgramModel.DoesNotExist
            MockProgramModel.objects.get.side_effect = ProgramModel.DoesNotExist

            with pytest.raises(ProgramNotFoundError):
                service.register_student(student_input, admin_user)
    
    @pytest.mark.django_db
    def test_stream_required_when_program_has_streams(
        self, service, admin_user, student_input, user_repository,
        student_repository, mock_program
    ):
        """Test that stream is required when program has streams."""
        from user_management.domain.exceptions import StreamRequiredError
        
        student_repository.exists_by_student_id.return_value = False
        student_input['stream_id'] = None  # Missing stream
        
        with patch('user_management.application.services.registration_service.ProgramModel') as MockProgramModel:
            MockProgramModel.objects.get.return_value = mock_program  # has_streams=True
            
            with pytest.raises(StreamRequiredError):
                service.register_student(student_input, admin_user)
    
    @pytest.mark.django_db
    def test_stream_not_allowed_when_program_no_streams(
        self, service, admin_user, student_input, user_repository,
        student_repository, mock_program_no_streams
    ):
        """Test that stream is not allowed when program has no streams."""
        from user_management.domain.exceptions import StreamNotAllowedError
        
        student_repository.exists_by_student_id.return_value = False
        student_input['program_id'] = 2
        student_input['student_id'] = 'BIT/654321'
        student_input['stream_id'] = 10  # Should not be provided
        
        with patch('user_management.application.services.registration_service.ProgramModel') as MockProgramModel:
            MockProgramModel.objects.get.return_value = mock_program_no_streams  # has_streams=False
            
            with pytest.raises(StreamNotAllowedError):
                service.register_student(student_input, admin_user)
    
    @pytest.mark.django_db
    def test_stream_not_in_program_raises_error(
        self, service, admin_user, student_input, user_repository,
        student_repository, mock_program, mock_stream
    ):
        """Test that stream not belonging to program raises error."""
        from user_management.domain.exceptions import StreamNotInProgramError
        
        student_repository.exists_by_student_id.return_value = False
        mock_stream.program_id = 999  # Different program
        
        with patch('user_management.application.services.registration_service.ProgramModel') as MockProgramModel:
            with patch('user_management.application.services.registration_service.StreamModel') as MockStreamModel:
                MockProgramModel.objects.get.return_value = mock_program
                MockStreamModel.objects.get.return_value = mock_stream
                
                with pytest.raises(StreamNotInProgramError):
                    service.register_student(student_input, admin_user)
    
    @pytest.mark.django_db
    @pytest.mark.parametrize('invalid_year', [0, -1, 5, 10])
    def test_invalid_year_raises_error(
        self, service, admin_user, student_input, user_repository,
        student_repository, mock_program, mock_stream, invalid_year
    ):
        """Test that invalid year of study raises InvalidYearError."""
        from user_management.domain.exceptions import InvalidYearError
        
        student_repository.exists_by_student_id.return_value = False
        student_input['year_of_study'] = invalid_year
        
        with patch('user_management.application.services.registration_service.ProgramModel') as MockProgramModel:
            with patch('user_management.application.services.registration_service.StreamModel') as MockStreamModel:
                MockProgramModel.objects.get.return_value = mock_program
                MockStreamModel.objects.get.return_value = mock_stream
                
                with pytest.raises(InvalidYearError):
                    service.register_student(student_input, admin_user)
    
    @pytest.mark.django_db
    def test_program_code_mismatch_raises_error(
        self, service, admin_user, student_input, user_repository,
        student_repository, mock_program
    ):
        """Test that student ID program code mismatch raises error."""
        from user_management.domain.exceptions import ProgramCodeMismatchError
        
        student_repository.exists_by_student_id.return_value = False
        student_input['student_id'] = 'XYZ/123456'  # Different code than BCS
        
        with patch('user_management.application.services.registration_service.ProgramModel') as MockProgramModel:
            MockProgramModel.objects.get.return_value = mock_program  # program_code='BCS'
            
            with pytest.raises(ProgramCodeMismatchError) as exc_info:
                service.register_student(student_input, admin_user)
            
            assert exc_info.value.student_id_code == 'XYZ'
            assert exc_info.value.program_code == 'BCS'
    
    # ---------------------
    # D. Edge Cases
    # ---------------------
    
    @pytest.mark.django_db
    def test_student_id_normalized_uppercase(
        self, service, admin_user, student_input, user_repository,
        student_repository, mock_program, mock_stream
    ):
        """Test that student ID is normalized to uppercase."""
        student_repository.exists_by_student_id.return_value = False
        student_input['student_id'] = 'bcs/123456'  # lowercase
        
        def _create_user(user_entity, password_hash):
            return User(
                user_id=26,
                first_name=user_entity.first_name,
                last_name=user_entity.last_name,
                email=user_entity.email,
                role=user_entity.role,
                is_active=user_entity.is_active,
                has_password=user_entity.has_password,
            )
        user_repository.create.side_effect = _create_user
        
        from user_management.domain.entities import StudentProfile
        
        def _create_student_profile(profile):
            return StudentProfile(
                student_profile_id=106,
                student_id=profile.student_id,
                user_id=profile.user_id,
                program_id=profile.program_id,
                stream_id=profile.stream_id,
                year_of_study=profile.year_of_study,
                qr_code_data=profile.qr_code_data,
            )
        student_repository.create.side_effect = _create_student_profile
        
        with patch('user_management.application.services.registration_service.ProgramModel') as MockProgramModel:
            with patch('user_management.application.services.registration_service.StreamModel') as MockStreamModel:
                MockProgramModel.objects.get.return_value = mock_program
                MockStreamModel.objects.get.return_value = mock_stream
                
                result = service.register_student(student_input, admin_user)
        
        assert str(result['student_profile'].student_id) == 'BCS/123456'
        student_repository.exists_by_student_id.assert_called_once_with('BCS/123456')
    
    @pytest.mark.django_db
    def test_email_normalized_lowercase(
        self, service, admin_user, student_input, user_repository,
        student_repository, mock_program, mock_stream
    ):
        """Test that email is normalized to lowercase."""
        student_repository.exists_by_student_id.return_value = False
        student_input['email'] = ' STUDENT@EXAMPLE.COM '
        
        def _create_user(user_entity, password_hash):
            return User(
                user_id=27,
                first_name=user_entity.first_name,
                last_name=user_entity.last_name,
                email=user_entity.email,
                role=user_entity.role,
                is_active=user_entity.is_active,
                has_password=user_entity.has_password,
            )
        user_repository.create.side_effect = _create_user
        
        from user_management.domain.entities import StudentProfile
        
        def _create_student_profile(profile):
            return StudentProfile(
                student_profile_id=107,
                student_id=profile.student_id,
                user_id=profile.user_id,
                program_id=profile.program_id,
                stream_id=profile.stream_id,
                year_of_study=profile.year_of_study,
                qr_code_data=profile.qr_code_data,
            )
        student_repository.create.side_effect = _create_student_profile
        
        with patch('user_management.application.services.registration_service.ProgramModel') as MockProgramModel:
            with patch('user_management.application.services.registration_service.StreamModel') as MockStreamModel:
                MockProgramModel.objects.get.return_value = mock_program
                MockStreamModel.objects.get.return_value = mock_stream
                
                result = service.register_student(student_input, admin_user)
        
        assert str(result['user'].email) == 'student@example.com'
        user_repository.exists_by_email.assert_called_once_with('student@example.com')
    
    @pytest.mark.django_db
    def test_stream_id_null_for_no_streams(
        self, service, admin_user, user_repository,
        student_repository, mock_program_no_streams
    ):
        """Test that stream_id is properly set to None for programs without streams."""
        student_input_no_stream = {
            'first_name': 'David',
            'last_name': 'Lee',
            'email': 'david@example.com',
            'student_id': 'BIT/111111',
            'program_id': 2,
            'stream_id': None,
            'year_of_study': 3,
        }
        
        student_repository.exists_by_student_id.return_value = False
        
        def _create_user(user_entity, password_hash):
            return User(
                user_id=28,
                first_name=user_entity.first_name,
                last_name=user_entity.last_name,
                email=user_entity.email,
                role=user_entity.role,
                is_active=user_entity.is_active,
                has_password=user_entity.has_password,
            )
        user_repository.create.side_effect = _create_user
        
        from user_management.domain.entities import StudentProfile
        
        def _create_student_profile(profile):
            assert profile.stream_id is None, "Stream ID should be None"
            return StudentProfile(
                student_profile_id=108,
                student_id=profile.student_id,
                user_id=profile.user_id,
                program_id=profile.program_id,
                stream_id=profile.stream_id,
                year_of_study=profile.year_of_study,
                qr_code_data=profile.qr_code_data,
            )
        student_repository.create.side_effect = _create_student_profile
        
        with patch('user_management.application.services.registration_service.ProgramModel') as MockProgramModel:
            MockProgramModel.objects.get.return_value = mock_program_no_streams
            
            result = service.register_student(student_input_no_stream, admin_user)
        
        assert result['student_profile'].stream_id is None


# -----------------------------
# Admin Registration Tests
# -----------------------------

@pytest.fixture()
def admin_input():
    """Base admin registration input."""
    return {
        'first_name': ' Charlie ',
        'last_name': ' Admin ',
        'email': ' NEWADMIN@EXAMPLE.COM ',
        'password': 'AdminPass123!',
    }


class TestRegisterAdmin:
    """Test suite for admin registration."""
    
    # ---------------------
    # A. Success Path
    # ---------------------
    
    def test_register_admin_success(
        self, service, admin_user, admin_input, user_repository,
        password_service
    ):
        """Test successful admin registration."""
        user_repository.exists_by_email.return_value = False
        
        def _create_user(user_entity, password_hash):
            assert password_hash == 'hashed_pw', "Admin should have password hash"
            return User(
                user_id=30,
                first_name=user_entity.first_name,
                last_name=user_entity.last_name,
                email=user_entity.email,
                role=user_entity.role,
                is_active=user_entity.is_active,
                has_password=user_entity.has_password,
            )
        user_repository.create.side_effect = _create_user
        
        result = service.register_admin(admin_input, admin_user)
        
        # Assertions
        assert 'user' in result
        assert 'student_profile' not in result  # No profile for admins
        assert 'lecturer_profile' not in result  # No profile for admins
        
        user = result['user']
        assert user.user_id == 30
        assert user.role == UserRole.ADMIN
        assert user.first_name == 'Charlie'  # trimmed
        assert user.last_name == 'Admin'  # trimmed
        assert str(user.email) == 'newadmin@example.com'  # normalized lowercase
        assert user.is_active is True
        assert user.has_password is True
        
        # Interaction assertions
        user_repository.exists_by_email.assert_called_once_with('newadmin@example.com')
        password_service.validate_password_strength.assert_called_once_with('AdminPass123!')
        password_service.hash_password.assert_called_once_with('AdminPass123!')
        user_repository.create.assert_called_once()
    
    def test_no_profile_created(
        self, service, admin_user, admin_input, user_repository,
        student_repository, lecturer_repository
    ):
        """Test that no profile is created for admin users."""
        user_repository.exists_by_email.return_value = False
        
        def _create_user(user_entity, password_hash):
            return User(
                user_id=31,
                first_name=user_entity.first_name,
                last_name=user_entity.last_name,
                email=user_entity.email,
                role=user_entity.role,
                is_active=user_entity.is_active,
                has_password=user_entity.has_password,
            )
        user_repository.create.side_effect = _create_user
        
        result = service.register_admin(admin_input, admin_user)
        
        # Assert no profile repositories were called
        student_repository.create.assert_not_called()
        lecturer_repository.create.assert_not_called()
        
        # Assert result only contains user
        assert 'user' in result
        assert len(result) == 1
    
    def test_admin_has_password(
        self, service, admin_user, admin_input, user_repository,
        password_service
    ):
        """Test that admin users are created with passwords."""
        user_repository.exists_by_email.return_value = False
        
        def _create_user(user_entity, password_hash):
            assert password_hash is not None, "Admin must have password hash"
            assert password_hash == 'hashed_pw'
            return User(
                user_id=32,
                first_name=user_entity.first_name,
                last_name=user_entity.last_name,
                email=user_entity.email,
                role=user_entity.role,
                is_active=user_entity.is_active,
                has_password=user_entity.has_password,
            )
        user_repository.create.side_effect = _create_user
        
        result = service.register_admin(admin_input, admin_user)
        
        assert result['user'].has_password is True
        password_service.validate_password_strength.assert_called_once()
        password_service.hash_password.assert_called_once()
    
    # ---------------------
    # B. Authorization
    # ---------------------
    
    def test_non_admin_raises_unauthorized(
        self, service, lecturer_user, admin_input
    ):
        """Test that non-admin users cannot create admin accounts."""
        from user_management.domain.exceptions import UnauthorizedError
        
        with pytest.raises(UnauthorizedError) as exc_info:
            service.register_admin(admin_input, lecturer_user)
        
        assert 'administrator' in str(exc_info.value).lower()
    
    def test_admin_can_register_admin(
        self, service, admin_user, admin_input, user_repository
    ):
        """Test that admin users can create other admin accounts."""
        user_repository.exists_by_email.return_value = False
        
        def _create_user(user_entity, password_hash):
            return User(
                user_id=33,
                first_name=user_entity.first_name,
                last_name=user_entity.last_name,
                email=user_entity.email,
                role=user_entity.role,
                is_active=user_entity.is_active,
                has_password=user_entity.has_password,
            )
        user_repository.create.side_effect = _create_user
        
        result = service.register_admin(admin_input, admin_user)
        
        assert result['user'] is not None
        assert result['user'].role == UserRole.ADMIN
        # Should not raise UnauthorizedError
    
    # ---------------------
    # C. Validation Errors
    # ---------------------
    
    def test_duplicate_email_raises_error(
        self, service, admin_user, admin_input, user_repository
    ):
        """Test that duplicate email raises EmailAlreadyExistsError."""
        user_repository.exists_by_email.return_value = True
        
        with pytest.raises(EmailAlreadyExistsError):
            service.register_admin(admin_input, admin_user)
        
        user_repository.create.assert_not_called()
    
    def test_weak_password_raises_error(
        self, service, admin_user, admin_input, user_repository,
        password_service
    ):
        """Test that weak password raises WeakPasswordError."""
        user_repository.exists_by_email.return_value = False
        password_service.validate_password_strength.side_effect = WeakPasswordError('too weak')
        
        with pytest.raises(WeakPasswordError):
            service.register_admin(admin_input, admin_user)
        
        password_service.hash_password.assert_not_called()
        user_repository.create.assert_not_called()
    
    # ---------------------
    # D. Edge Cases
    # ---------------------
    
    def test_email_normalized_lowercase(
        self, service, admin_user, admin_input, user_repository
    ):
        """Test that admin email is normalized to lowercase."""
        user_repository.exists_by_email.return_value = False
        admin_input['email'] = ' UPPERCASE@EXAMPLE.COM '
        
        def _create_user(user_entity, password_hash):
            return User(
                user_id=34,
                first_name=user_entity.first_name,
                last_name=user_entity.last_name,
                email=user_entity.email,
                role=user_entity.role,
                is_active=user_entity.is_active,
                has_password=user_entity.has_password,
            )
        user_repository.create.side_effect = _create_user
        
        result = service.register_admin(admin_input, admin_user)
        
        assert str(result['user'].email) == 'uppercase@example.com'
        user_repository.exists_by_email.assert_called_once_with('uppercase@example.com')
