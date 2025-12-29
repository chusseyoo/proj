"""Token validation service for JWT token verification."""
from __future__ import annotations
from typing import Dict, Any

from ..exceptions import InvalidTokenError, TokenExpiredError


class TokenValidator:
    """Validates and decodes attendance JWT tokens.
    
    Responsibilities:
    - Verify token signature (not forged)
    - Check token expiry (exp claim)
    - Validate required claims (student_profile_id, session_id)
    """
    
    REQUIRED_CLAIMS = {"student_profile_id", "session_id"}
    
    def __init__(self, secret_key: str):
        """Initialize validator with secret key.
        
        Args:
            secret_key: Secret key used to sign tokens
        
        Raises:
            ImportError: If PyJWT is not installed
        """
        self.secret_key = secret_key
        try:
            import jwt
            self.jwt = jwt
        except ImportError:
            raise ImportError("PyJWT library required: pip install PyJWT")
    
    def validate_and_decode(self, token: str) -> Dict[str, Any]:
        """Validate token and return decoded payload.
        
        Performs:
        1. Format validation (must have 3 parts: header.payload.signature)
        2. Signature verification (must match secret key)
        3. Expiry check (must not be expired)
        4. Required claims validation (must contain student_profile_id, session_id)
        
        Args:
            token: JWT token string from email link
        
        Returns:
            Decoded payload dictionary with claims
        
        Raises:
            InvalidTokenError: Token format/signature invalid or missing claims
            TokenExpiredError: Token has passed expiry time
        """
        if not token or not isinstance(token, str):
            raise InvalidTokenError("Token must be non-empty string")
        
        # Check format (should have 3 parts separated by dots)
        parts = token.split(".")
        if len(parts) != 3:
            raise InvalidTokenError(
                "Invalid token format: must be header.payload.signature"
            )
        
        try:
            # Decode and verify signature
            payload = self.jwt.decode(
                token,
                self.secret_key,
                algorithms=["HS256"],
            )
        except self.jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except self.jwt.InvalidSignatureError:
            raise InvalidTokenError(
                "Invalid token signature: tampered or wrong secret key"
            )
        except self.jwt.DecodeError as e:
            raise InvalidTokenError(f"Failed to decode token: {str(e)}")
        except Exception as e:
            raise InvalidTokenError(f"Token validation failed: {str(e)}")
        
        # Validate required claims are present
        missing_claims = self.REQUIRED_CLAIMS - set(payload.keys())
        if missing_claims:
            raise InvalidTokenError(
                f"Token missing required claims: {', '.join(missing_claims)}"
            )
        
        return payload
