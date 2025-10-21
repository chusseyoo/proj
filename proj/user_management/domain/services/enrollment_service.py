"""
Domain service for enrollment-related operations.

Handles business logic around student enrollment in programs and streams.
"""
from typing import Optional

from ..exceptions import (
    InvalidYearError,
    StreamRequiredError,
    StreamNotAllowedError,
)


class EnrollmentService:
    """
    Domain service for student enrollment business logic.
    
    Responsibilities:
    - Validate year of study progression
    - Enforce stream assignment rules based on program
    - Coordinate enrollment constraints
    """
    
    MIN_YEAR = 1
    MAX_YEAR = 4
    
    @staticmethod
    def validate_year_of_study(year: int) -> None:
        """
        Validate year of study is within valid range.
        
        Business rule: Year must be between 1 and 4 (inclusive).
        
        Args:
            year: Year of study
            
        Raises:
            InvalidYearError: If year is outside valid range
        """
        if not (EnrollmentService.MIN_YEAR <= year <= EnrollmentService.MAX_YEAR):
            raise InvalidYearError(year)
    
    @staticmethod
    def validate_stream_requirement(
        program_has_streams: bool,
        stream_id: Optional[int]
    ) -> None:
        """
        Validate stream assignment based on program configuration.
        
        Business rules:
        - If program has streams, stream_id is REQUIRED
        - If program has no streams, stream_id must be NULL
        
        Args:
            program_has_streams: Whether program has stream subdivisions
            stream_id: Stream assignment (can be None)
            
        Raises:
            StreamRequiredError: If program has streams but stream_id is None
            StreamNotAllowedError: If program has no streams but stream_id provided
        """
        if program_has_streams and stream_id is None:
            raise StreamRequiredError(
                "This program requires a stream assignment"
            )
        
        if not program_has_streams and stream_id is not None:
            raise StreamNotAllowedError(
                "This program does not have streams"
            )
    
    @staticmethod
    def can_progress_to_year(current_year: int, target_year: int) -> bool:
        """
        Determine if student can progress to target year.
        
        Business rule: Students can only progress one year at a time
        or stay in current year (repeat).
        
        Args:
            current_year: Student's current year
            target_year: Desired year to progress to
            
        Returns:
            True if progression is allowed
        """
        # Can stay in same year (repeat) or progress by 1
        return target_year in (current_year, current_year + 1) and \
               EnrollmentService.MIN_YEAR <= target_year <= EnrollmentService.MAX_YEAR
