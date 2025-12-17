"""JWT token generation and validation service."""
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from email_notifications.domain.exceptions import (
    InvalidTokenError,
    ExpiredTokenError,
    InvalidTokenExpiryError,
    TokenGenerationError,
)


class JWTTokenService:
    """Generates and validates JWT tokens for attendance links.

    Responsibilities:
    - Generate signed JWT tokens with student_profile_id and session_id
    - Validate token signature (hasn't been tampered with)
    - Check token expiry
    - Extract claims from valid tokens

    Security: Uses HS256 (HMAC-SHA256) with secret key.
    """

    ALGORITHM = "HS256"
    REQUIRED_CLAIMS = ["student_profile_id", "session_id"]

    def __init__(self, secret_key: str):
        """Initialize with secret key for token signing.

        Args:
            secret_key: Secret key for HMAC (from settings.JWT_SECRET_KEY)

        Raises:
            ImportError: If PyJWT library not installed
        """
        if not secret_key:
            raise ValueError("Secret key cannot be empty")

        self.secret_key = secret_key

        try:
            import jwt
            self.jwt = jwt
        except ImportError:
            raise ImportError("PyJWT library required. Install with: pip install PyJWT")

    def generate_token(
        self,
        student_profile_id: int,
        session_id: int,
        expires_at: datetime,
    ) -> str:
        """Generate JWT token for attendance link.

        Creates a signed token with payload:
        {
          "student_profile_id": 123,
          "session_id": 456,
          "iat": 1729339200,
          "exp": 1729342800
        }

        Args:
            student_profile_id: Student's profile ID
            session_id: Session ID
            expires_at: Token expiration time (datetime with timezone)

        Returns:
            Encoded JWT token string (~200-500 chars)

        Raises:
            InvalidTokenExpiryError: Expiry is in the past
            TokenGenerationError: Failed to generate token
        """
        # Validate expiry
        now = datetime.now(timezone.utc)
        if isinstance(expires_at, datetime):
            exp_time = expires_at
        else:
            raise InvalidTokenExpiryError("expires_at must be a datetime object")

        if exp_time <= now:
            raise InvalidTokenExpiryError(
                f"Token expiry must be in future, got {exp_time} (now: {now})"
            )

        # Convert datetime to Unix timestamp for JWT exp claim
        exp_timestamp = int(exp_time.timestamp())

        payload = {
            "student_profile_id": student_profile_id,
            "session_id": session_id,
            "exp": exp_timestamp,
        }

        try:
            token = self.jwt.encode(
                payload,
                self.secret_key,
                algorithm=self.ALGORITHM,
            )
            return token
        except Exception as e:
            raise TokenGenerationError(f"Failed to generate token: {str(e)}")

    def validate_token(self, token: str) -> bool:
        """Check if token is valid (signature and expiry).

        Validation steps:
        1. Format check (3 parts: header.payload.signature)
        2. Signature verification
        3. Expiry check

        Args:
            token: JWT token string

        Returns:
            True if valid, False otherwise
        """
        try:
            self.decode_token(token)
            return True
        except (InvalidTokenError, ExpiredTokenError):
            return False

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Extract and validate payload from token.

        Args:
            token: JWT token string

        Returns:
            Decoded payload dictionary

        Raises:
            InvalidTokenError: Token format, signature invalid
            ExpiredTokenError: Token has expired
        """
        if not token or not isinstance(token, str):
            raise InvalidTokenError("Token must be non-empty string")

        # Check format (should have 3 parts)
        parts = token.split(".")
        if len(parts) != 3:
            raise InvalidTokenError(
                "Invalid token format (must be header.payload.signature)"
            )

        try:
            # Decode and verify signature
            payload = self.jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.ALGORITHM],
            )
        except self.jwt.ExpiredSignatureError:
            raise ExpiredTokenError("Token has expired")
        except self.jwt.InvalidSignatureError:
            raise InvalidTokenError(
                "Invalid token signature (tampered or wrong secret)"
            )
        except self.jwt.DecodeError as e:
            raise InvalidTokenError(f"Failed to decode token: {str(e)}")
        except Exception as e:
            raise InvalidTokenError(f"Token validation failed: {str(e)}")

        # Validate required claims
        for claim in self.REQUIRED_CLAIMS:
            if claim not in payload:
                raise InvalidTokenError(f"Token missing required claim: {claim}")

        return payload

    def is_token_expired(self, token: str) -> bool:
        """Quick expiry check without full validation.

        Args:
            token: JWT token string

        Returns:
            True if expired, False otherwise
        """
        try:
            self.jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.ALGORITHM],
            )
            return False
        except self.jwt.ExpiredSignatureError:
            return True
        except Exception:
            # Any other error means we can't determine expiry
            # Caller should do full validation to get proper error
            return False

    def extract_claims_unverified(self, token: str) -> Optional[Dict[str, Any]]:
        """Extract claims without verification (for debugging only).

        WARNING: Does NOT verify signature - use only for logging/debugging.

        Args:
            token: JWT token string

        Returns:
            Claims dictionary, or None if token is malformed
        """
        try:
            payload = self.jwt.decode(
                token,
                options={"verify_signature": False},
            )
            return payload
        except Exception:
            return None
