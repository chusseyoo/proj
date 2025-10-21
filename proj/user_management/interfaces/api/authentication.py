"""
JWT Authentication Backend for DRF.

Extracts and validates JWT tokens from Authorization header,
sets request.user to authenticated user entity.
"""
from rest_framework import authentication, exceptions
from django.conf import settings

from ...application.services import AuthenticationService
from ...infrastructure.repositories import UserRepository, StudentProfileRepository
from ...application.services import PasswordService
from ...domain.exceptions import InvalidTokenError, ExpiredTokenError, UserNotFoundError


class JWTAuthentication(authentication.BaseAuthentication):
    """
    Custom JWT authentication for DRF.
    
    Expects: Authorization: Bearer <token>
    Validates access tokens via AuthenticationService.
    Sets request.user to domain User entity.
    """
    
    keyword = 'Bearer'
    
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            return None  # No auth header, allow other auth methods
        
        parts = auth_header.split()
        
        if len(parts) != 2 or parts[0] != self.keyword:
            return None  # Not Bearer token format
        
        token = parts[1]
        
        try:
            # Validate token using AuthenticationService
            auth_service = self._get_auth_service()
            decoded = auth_service.validate_token(token, token_type='access')
            
            # Extract user_id from token
            user_id = decoded.get('user_id')
            if not user_id:
                raise exceptions.AuthenticationFailed('Invalid token payload')
            
            # Fetch user entity
            user_repo = UserRepository()
            user = user_repo.get_by_id(user_id)
            
            if not user.is_active:
                raise exceptions.AuthenticationFailed('User account is deactivated')
            
            # Return user and token (DRF convention)
            return (user, token)
            
        except ExpiredTokenError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')
        except UserNotFoundError:
            raise exceptions.AuthenticationFailed('User not found')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Authentication failed: {str(e)}')
    
    def authenticate_header(self, request):
        """
        Return WWW-Authenticate header value for 401 responses.
        """
        return f'{self.keyword} realm="api"'
    
    def _get_auth_service(self):
        """Instantiate AuthenticationService with dependencies."""
        user_repo = UserRepository()
        student_repo = StudentProfileRepository()
        password_service = PasswordService(user_repository=user_repo)
        
        return AuthenticationService(
            user_repository=user_repo,
            password_service=password_service,
            student_repository=student_repo,
            refresh_store=None,  # Optional, not wired yet
        )
