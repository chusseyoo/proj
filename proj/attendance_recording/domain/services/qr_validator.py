"""QR code validation service."""
from __future__ import annotations
import re
from typing import Tuple

from ..exceptions import QRMismatchError


class QRCodeValidator:
    """Validates QR code data (student ID format and matching).
    
    QR Code Format: ^[A-Z]{3}/[0-9]{6}$
    Example: BCS/234344
    
    Business Rules:
    - QR code contains student ID (3 uppercase letters + slash + 6 digits)
    - Scanned student ID must match StudentProfile.student_id from token
    - This prevents email forwarding fraud
    """
    
    # QR code pattern: 3 uppercase letters, slash, 6 digits (e.g., BCS/234344)
    PATTERN = r"^[A-Z]{3}/[0-9]{6}$"
    
    @classmethod
    def validate_format(cls, qr_data: str) -> str:
        """Validate QR code format.
        
        Args:
            qr_data: Raw data extracted from QR code scan
        
        Returns:
            Validated student ID string
        
        Raises:
            QRMismatchError: If format is invalid
        """
        if not isinstance(qr_data, str):
            raise QRMismatchError(
                f"QR data must be string, got {type(qr_data).__name__}"
            )
        
        qr_data = qr_data.strip()
        
        if not re.match(cls.PATTERN, qr_data):
            raise QRMismatchError(
                f"Invalid QR format. Expected format: ABC/123456, got: {qr_data}"
            )
        
        return qr_data
    
    @staticmethod
    def verify_match(
        scanned_student_id: str,
        token_student_id: str,
    ) -> None:
        """Verify that scanned student ID matches token student ID.
        
        Anti-Fraud Check:
        Prevents a student from using another student's email link
        to mark attendance for that student.
        
        Args:
            scanned_student_id: Student ID from QR code scan
            token_student_id: Student ID from JWT token payload
        
        Raises:
            QRMismatchError: If they don't match (fraud attempt)
        """
        if scanned_student_id != token_student_id:
            raise QRMismatchError(
                f"Scanned QR ({scanned_student_id}) does not match "
                f"email token student ({token_student_id}). "
                f"Possible fraud: using someone else's email link?"
            )
