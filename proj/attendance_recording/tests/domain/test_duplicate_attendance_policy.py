import pytest

from attendance_recording.domain.services.duplicate_attendance_policy import (
    DuplicateAttendancePolicy,
)
from attendance_recording.domain.exceptions import DuplicateAttendanceError


class TestDuplicateAttendancePolicy:
    def test_no_existing_attendance_passes(self):
        DuplicateAttendancePolicy.check_duplicate(None)

    def test_existing_attendance_raises(self):
        with pytest.raises(DuplicateAttendanceError):
            DuplicateAttendancePolicy.check_duplicate({"id": 1})
