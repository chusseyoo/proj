"""REST API Serializers for Academic Structure.

This module provides serializers for converting DTOs to/from JSON for the REST API.
Follows specifications from api_guide.md.
"""

from rest_framework import serializers


# ============================================================================
# PROGRAM SERIALIZERS
# ============================================================================

class ProgramSerializer(serializers.Serializer):
    """Serializer for Program DTO.
    
    Maps to ProgramDTO from application layer.
    Used for all Program API endpoints.
    """
    program_id = serializers.IntegerField(read_only=True)
    program_name = serializers.CharField(max_length=200, required=True)
    program_code = serializers.CharField(max_length=3, min_length=3, required=True)
    department_name = serializers.CharField(max_length=50, min_length=5, required=True)
    has_streams = serializers.BooleanField(default=False)

    def validate_program_code(self, value):
        """Validate program_code format: exactly 3 uppercase letters."""
        value = value.strip().upper()
        
        if not value.isalpha():
            raise serializers.ValidationError(
                "program_code must contain only letters (no numbers or symbols)"
            )
        
        if len(value) != 3:
            raise serializers.ValidationError(
                "program_code must be exactly 3 letters (e.g., BCS, BEG, DIT)"
            )
        
        return value

    def validate_program_name(self, value):
        """Validate and normalize program_name."""
        value = value.strip()
        
        if len(value) < 5:
            raise serializers.ValidationError(
                "program_name must be at least 5 characters"
            )
        
        if len(value) > 200:
            raise serializers.ValidationError(
                "program_name cannot exceed 200 characters"
            )
        
        return value

    def validate_department_name(self, value):
        """Validate and normalize department_name."""
        value = value.strip()
        
        if len(value) < 5:
            raise serializers.ValidationError(
                "department_name must be at least 5 characters"
            )
        
        if len(value) > 50:
            raise serializers.ValidationError(
                "department_name cannot exceed 50 characters"
            )
        
        return value


# ============================================================================
# STREAM SERIALIZERS
# ============================================================================

class StreamSerializer(serializers.Serializer):
    """Serializer for Stream DTO.
    
    Maps to StreamDTO from application layer.
    Used for all Stream API endpoints.
    """
    stream_id = serializers.IntegerField(read_only=True)
    stream_name = serializers.CharField(max_length=50, required=True)
    program_id = serializers.IntegerField(required=True)
    program_code = serializers.CharField(max_length=6, read_only=True)
    year_of_study = serializers.IntegerField(min_value=1, max_value=4, required=True)

    def validate_stream_name(self, value):
        """Validate and normalize stream_name."""
        value = value.strip()
        
        if len(value) < 1:
            raise serializers.ValidationError(
                "stream_name cannot be empty"
            )
        
        if len(value) > 50:
            raise serializers.ValidationError(
                "stream_name cannot exceed 50 characters"
            )
        
        return value


# ============================================================================
# COURSE SERIALIZERS
# ============================================================================

class CourseSerializer(serializers.Serializer):
    """Serializer for Course DTO.
    
    Maps to CourseDTO from application layer.
    Used for all Course API endpoints.
    """
    course_id = serializers.IntegerField(read_only=True)
    course_code = serializers.CharField(max_length=6, required=True)
    course_name = serializers.CharField(max_length=200, required=True)
    program_id = serializers.IntegerField(required=True)
    program_code = serializers.CharField(max_length=6, read_only=True)
    department_name = serializers.CharField(max_length=50, min_length=5, required=True)
    lecturer_id = serializers.IntegerField(required=False, allow_null=True)
    lecturer_name = serializers.CharField(max_length=200, read_only=True, required=False, allow_null=True)

    def validate_course_code(self, value):
        """Validate course_code format: exactly 6 uppercase alphanumeric characters."""
        import re
        
        value = value.strip().upper()
        
        # Pattern: exactly 6 uppercase alphanumeric characters
        pattern = r'^[A-Z0-9]{6}$'
        
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "course_code must be exactly 6 uppercase alphanumeric characters (e.g., BCS012, BEG230, DIT410)"
            )
        
        return value

    def validate_course_name(self, value):
        """Validate and normalize course_name."""
        value = value.strip()
        
        if len(value) < 3:
            raise serializers.ValidationError(
                "course_name must be at least 3 characters"
            )
        
        if len(value) > 200:
            raise serializers.ValidationError(
                "course_name cannot exceed 200 characters"
            )
        
        return value

    def validate_department_name(self, value):
        """Validate and normalize department_name."""
        value = value.strip()
        
        if len(value) < 5:
            raise serializers.ValidationError(
                "department_name must be at least 5 characters"
            )
        
        if len(value) > 50:
            raise serializers.ValidationError(
                "department_name cannot exceed 50 characters"
            )
        
        return value


class AssignLecturerSerializer(serializers.Serializer):
    """Serializer for assigning a lecturer to a course.
    
    Used for POST /courses/{id}/assign-lecturer endpoint.
    """
    lecturer_id = serializers.IntegerField(required=True)

    def validate_lecturer_id(self, value):
        """Validate lecturer_id is positive."""
        if value <= 0:
            raise serializers.ValidationError(
                "lecturer_id must be a positive integer"
            )
        
        return value


# ============================================================================
# PAGINATION SERIALIZER
# ============================================================================

class PaginatedResponseSerializer(serializers.Serializer):
    """Serializer for paginated API responses.
    
    Standard pagination format per api_guide.md:
    {
      "results": [...],
      "total_count": 123,
      "page": 1,
      "page_size": 20,
      "total_pages": 7,
      "has_next": true,
      "has_previous": false
    }
    """
    results = serializers.ListField()
    total_count = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    has_next = serializers.BooleanField()
    has_previous = serializers.BooleanField()


# ============================================================================
# ERROR SERIALIZER
# ============================================================================

class ErrorSerializer(serializers.Serializer):
    """Serializer for error responses.
    
    Standard error format per api_guide.md:
    {
      "error": {
        "code": "ProgramNotFoundError",
        "message": "Program not found",
        "details": { "program_id": 999 }
      }
    }
    """
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(required=False, allow_null=True)
