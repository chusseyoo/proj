"""Tests for JWTTokenService domain service."""
import pytest
from datetime import datetime, timezone, timedelta
import jwt as pyjwt

from email_notifications.domain.services import JWTTokenService
from email_notifications.domain.exceptions import (
    InvalidTokenError,
    ExpiredTokenError,
    InvalidTokenExpiryError,
    TokenGenerationError,
)


class TestJWTTokenService:
    """Test suite for JWT token generation and validation."""

    @pytest.fixture
    def jwt_service(self):
        """Create JWT service with test secret key."""
        return JWTTokenService(secret_key="test-secret-key-do-not-use-in-prod")

    @pytest.fixture
    def future_expiry(self):
        """Expiry time 1 hour in the future."""
        return datetime.now(timezone.utc) + timedelta(hours=1)

    # ==================== Token Generation Tests ====================

    def test_generate_token_returns_string(self, jwt_service, future_expiry):
        """Token generation should return a string."""
        token = jwt_service.generate_token(
            student_profile_id=123,
            session_id=456,
            expires_at=future_expiry,
        )
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are typically 200+ chars

    def test_generate_token_creates_valid_jwt(self, jwt_service, future_expiry):
        """Generated token should be decodable and contain correct payload."""
        token = jwt_service.generate_token(
            student_profile_id=123,
            session_id=456,
            expires_at=future_expiry,
        )
        
        # Decode token without verification (just to check payload)
        payload = pyjwt.decode(token, options={"verify_signature": False})
        
        assert payload["student_profile_id"] == 123
        assert payload["session_id"] == 456
        assert "exp" in payload

    def test_generate_token_includes_required_claims(self, jwt_service, future_expiry):
        """Token payload must include student_profile_id and session_id."""
        token = jwt_service.generate_token(
            student_profile_id=789,
            session_id=999,
            expires_at=future_expiry,
        )
        
        payload = jwt_service.decode_token(token)
        
        assert payload["student_profile_id"] == 789
        assert payload["session_id"] == 999

    def test_generate_token_includes_expiry_claim(self, jwt_service, future_expiry):
        """Token must include exp claim matching expires_at."""
        token = jwt_service.generate_token(
            student_profile_id=123,
            session_id=456,
            expires_at=future_expiry,
        )
        
        payload = pyjwt.decode(token, options={"verify_signature": False})
        
        # Verify exp is close to expires_at (within 1 second)
        exp_from_token = payload["exp"]
        exp_expected = int(future_expiry.timestamp())
        assert abs(exp_from_token - exp_expected) <= 1

    def test_generate_token_uses_correct_algorithm(self, jwt_service, future_expiry):
        """Token must be signed with HS256."""
        token = jwt_service.generate_token(
            student_profile_id=123,
            session_id=456,
            expires_at=future_expiry,
        )
        
        # Decode header to check algorithm
        header = pyjwt.get_unverified_header(token)
        assert header["alg"] == "HS256"
        assert header["typ"] == "JWT"

    def test_generate_token_with_past_expiry_raises_error(self, jwt_service):
        """Generating token with past expiry time should raise InvalidTokenExpiryError."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
        with pytest.raises(InvalidTokenExpiryError):
            jwt_service.generate_token(
                student_profile_id=123,
                session_id=456,
                expires_at=past_time,
            )

    def test_generate_token_without_secret_key_raises_error(self):
        """Creating service without secret key should raise ValueError."""
        with pytest.raises(ValueError):
            JWTTokenService(secret_key="")

    def test_generate_token_verifiable_with_service_key(self, jwt_service, future_expiry):
        """Token can be verified with service's secret key."""
        token = jwt_service.generate_token(
            student_profile_id=123,
            session_id=456,
            expires_at=future_expiry,
        )
        
        # Should not raise exception
        payload = pyjwt.decode(
            token,
            jwt_service.secret_key,
            algorithms=["HS256"],
        )
        
        assert payload["student_profile_id"] == 123

    # ==================== Token Validation Tests ====================

    def test_validate_token_returns_true_for_valid_token(self, jwt_service, future_expiry):
        """Validating a freshly generated token should return True."""
        token = jwt_service.generate_token(
            student_profile_id=123,
            session_id=456,
            expires_at=future_expiry,
        )
        
        assert jwt_service.validate_token(token) is True

    def test_validate_token_returns_false_for_invalid_signature(self, jwt_service, future_expiry):
        """Token with tampered payload should return False."""
        token = jwt_service.generate_token(
            student_profile_id=123,
            session_id=456,
            expires_at=future_expiry,
        )
        
        # Modify token by changing one character
        tampered = token[:-10] + "corrupted!"
        
        assert jwt_service.validate_token(tampered) is False

    def test_validate_token_returns_false_for_empty_string(self, jwt_service):
        """Empty token should return False."""
        assert jwt_service.validate_token("") is False

    def test_validate_token_returns_false_for_none(self, jwt_service):
        """None token should return False."""
        assert jwt_service.validate_token(None) is False

    # ==================== Token Decoding Tests ====================

    def test_decode_token_returns_payload_dict(self, jwt_service, future_expiry):
        """Decoding should return dictionary with payload."""
        token = jwt_service.generate_token(
            student_profile_id=123,
            session_id=456,
            expires_at=future_expiry,
        )
        
        payload = jwt_service.decode_token(token)
        
        assert isinstance(payload, dict)
        assert payload["student_profile_id"] == 123
        assert payload["session_id"] == 456

    def test_decode_token_includes_all_claims(self, jwt_service, future_expiry):
        """Decoded payload must include all required claims."""
        token = jwt_service.generate_token(
            student_profile_id=789,
            session_id=999,
            expires_at=future_expiry,
        )
        
        payload = jwt_service.decode_token(token)
        
        assert "student_profile_id" in payload
        assert "session_id" in payload
        assert "exp" in payload

    def test_decode_token_raises_invalid_error_for_tampered_token(self, jwt_service, future_expiry):
        """Decoding tampered token should raise InvalidTokenError."""
        token = jwt_service.generate_token(
            student_profile_id=123,
            session_id=456,
            expires_at=future_expiry,
        )
        
        tampered = token[:-10] + "corrupted!"
        
        with pytest.raises(InvalidTokenError):
            jwt_service.decode_token(tampered)

    def test_decode_token_raises_invalid_error_for_malformed_token(self, jwt_service):
        """Decoding malformed token should raise InvalidTokenError."""
        with pytest.raises(InvalidTokenError):
            jwt_service.decode_token("not.a.jwt")

    def test_decode_token_raises_invalid_error_for_empty_token(self, jwt_service):
        """Decoding empty token should raise InvalidTokenError."""
        with pytest.raises(InvalidTokenError):
            jwt_service.decode_token("")

    def test_decode_token_missing_student_profile_id_raises_error(self, jwt_service):
        """Token missing student_profile_id claim should raise InvalidTokenError."""
        # Manually create token without required claim
        payload = {
            "session_id": 456,
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        }
        token = pyjwt.encode(
            payload,
            jwt_service.secret_key,
            algorithm="HS256",
        )
        
        with pytest.raises(InvalidTokenError) as exc_info:
            jwt_service.decode_token(token)
        
        assert "student_profile_id" in str(exc_info.value)

    def test_decode_token_missing_session_id_raises_error(self, jwt_service):
        """Token missing session_id claim should raise InvalidTokenError."""
        payload = {
            "student_profile_id": 123,
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        }
        token = pyjwt.encode(
            payload,
            jwt_service.secret_key,
            algorithm="HS256",
        )
        
        with pytest.raises(InvalidTokenError) as exc_info:
            jwt_service.decode_token(token)
        
        assert "session_id" in str(exc_info.value)

    # ==================== Expiry Checking Tests ====================

    def test_is_token_expired_returns_false_for_valid_token(self, jwt_service, future_expiry):
        """Valid token should return False."""
        token = jwt_service.generate_token(
            student_profile_id=123,
            session_id=456,
            expires_at=future_expiry,
        )
        
        assert jwt_service.is_token_expired(token) is False

    def test_is_token_expired_returns_true_for_expired_token(self, jwt_service):
        """Expired token should return True."""
        past_expiry = datetime.now(timezone.utc) - timedelta(seconds=1)
        
        # Manually create expired token
        payload = {
            "student_profile_id": 123,
            "session_id": 456,
            "exp": int(past_expiry.timestamp()),
        }
        token = pyjwt.encode(
            payload,
            jwt_service.secret_key,
            algorithm="HS256",
        )
        
        assert jwt_service.is_token_expired(token) is True

    def test_is_token_expired_returns_false_for_malformed_token(self, jwt_service):
        """Malformed token should return False (graceful degradation)."""
        assert jwt_service.is_token_expired("not.a.token") is False

    # ==================== Unverified Claims Extraction ====================

    def test_extract_claims_unverified_returns_payload(self, jwt_service, future_expiry):
        """Extracting without verification should return payload."""
        token = jwt_service.generate_token(
            student_profile_id=123,
            session_id=456,
            expires_at=future_expiry,
        )
        
        claims = jwt_service.extract_claims_unverified(token)
        
        assert claims is not None
        assert claims["student_profile_id"] == 123
        assert claims["session_id"] == 456

    def test_extract_claims_unverified_works_for_expired_token(self, jwt_service):
        """Should extract claims even from expired token (no verification)."""
        past_expiry = datetime.now(timezone.utc) - timedelta(seconds=1)
        
        payload = {
            "student_profile_id": 123,
            "session_id": 456,
            "exp": int(past_expiry.timestamp()),
        }
        token = pyjwt.encode(
            payload,
            jwt_service.secret_key,
            algorithm="HS256",
        )
        
        claims = jwt_service.extract_claims_unverified(token)
        
        assert claims["student_profile_id"] == 123

    def test_extract_claims_unverified_returns_none_for_malformed_token(self, jwt_service):
        """Malformed token should return None (graceful)."""
        claims = jwt_service.extract_claims_unverified("not.a.token")
        assert claims is None

    # ==================== Integration Tests ====================

    def test_token_roundtrip_generate_validate_decode(self, jwt_service, future_expiry):
        """Full roundtrip: generate → validate → decode."""
        original_student_id = 123
        original_session_id = 456
        
        # Generate
        token = jwt_service.generate_token(
            student_profile_id=original_student_id,
            session_id=original_session_id,
            expires_at=future_expiry,
        )
        
        # Validate
        assert jwt_service.validate_token(token) is True
        
        # Decode
        payload = jwt_service.decode_token(token)
        
        assert payload["student_profile_id"] == original_student_id
        assert payload["session_id"] == original_session_id

    def test_different_secrets_cannot_decode_tokens(self, future_expiry):
        """Token from service A should fail validation in service B with different secret."""
        service_a = JWTTokenService(secret_key="secret-a")
        service_b = JWTTokenService(secret_key="secret-b")
        
        token = service_a.generate_token(
            student_profile_id=123,
            session_id=456,
            expires_at=future_expiry,
        )
        
        with pytest.raises(InvalidTokenError):
            service_b.decode_token(token)
