import pytest
from datetime import datetime, timedelta, timezone
import jwt

from attendance_recording.domain.services.token_validator import TokenValidator
from attendance_recording.domain.exceptions import InvalidTokenError, TokenExpiredError


class TestTokenValidator:
    def test_validate_and_decode_success(self, jwt_secret):
        payload = {
            "student_profile_id": 123,
            "session_id": 456,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")
        validator = TokenValidator(secret_key=jwt_secret)
        decoded = validator.validate_and_decode(token)
        assert decoded["student_profile_id"] == 123
        assert decoded["session_id"] == 456

    def test_invalid_signature_raises(self, jwt_secret):
        payload = {
            "student_profile_id": 1,
            "session_id": 2,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
        token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
        validator = TokenValidator(secret_key=jwt_secret)
        with pytest.raises(InvalidTokenError):
            validator.validate_and_decode(token)

    def test_expired_token_raises(self, jwt_secret):
        payload = {
            "student_profile_id": 1,
            "session_id": 2,
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        }
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")
        validator = TokenValidator(secret_key=jwt_secret)
        with pytest.raises(TokenExpiredError):
            validator.validate_and_decode(token)

    def test_missing_claims_raises(self, jwt_secret):
        payload = {
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")
        validator = TokenValidator(secret_key=jwt_secret)
        with pytest.raises(InvalidTokenError):
            validator.validate_and_decode(token)

    def test_bad_format_raises(self, jwt_secret):
        validator = TokenValidator(secret_key=jwt_secret)
        with pytest.raises(InvalidTokenError):
            validator.validate_and_decode("not.a.valid.token")
