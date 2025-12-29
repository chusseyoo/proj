import pytest

from attendance_recording.domain.services.qr_validator import QRCodeValidator
from attendance_recording.domain.exceptions import QRMismatchError


class TestQRCodeValidator:
    def test_validate_format_success(self):
        assert QRCodeValidator.validate_format("BCS/234344") == "BCS/234344"

    @pytest.mark.parametrize("bad", [
        "bcs/234344",   # lowercase
        "BCS234344",    # missing slash
        "BCS/12345",    # too few digits
        "BCS/1234567",  # too many digits
        123456,          # not a string
    ])
    def test_validate_format_invalid(self, bad):
        with pytest.raises(QRMismatchError):
            QRCodeValidator.validate_format(bad)

    def test_verify_match_success(self):
        QRCodeValidator.verify_match("BCS/234344", "BCS/234344")

    def test_verify_match_mismatch_raises(self):
        with pytest.raises(QRMismatchError):
            QRCodeValidator.verify_match("BCS/234344", "MIT/999999")
