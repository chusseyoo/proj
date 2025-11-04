"""Use cases for the academic structure application layer."""

# Import all use case modules to make them available as subpackages
from . import program, stream, course

# Import all use cases for convenient access
from .program import (
    GetProgramUseCase,
    GetProgramByCodeUseCase,
    ListProgramsUseCase,
    CreateProgramUseCase,
    UpdateProgramUseCase,
    DeleteProgramUseCase,
)

from .stream import (
    GetStreamUseCase,
    ListStreamsByProgramUseCase,
    CreateStreamUseCase,
    UpdateStreamUseCase,
    DeleteStreamUseCase,
)

from .course import (
    GetCourseUseCase,
    GetCourseByCodeUseCase,
    ListCoursesUseCase,
    ListUnassignedCoursesUseCase,
    CreateCourseUseCase,
    UpdateCourseUseCase,
    DeleteCourseUseCase,
    AssignLecturerUseCase,
    UnassignLecturerUseCase,
)

__all__ = [
    # Program use cases
    'GetProgramUseCase',
    'GetProgramByCodeUseCase',
    'ListProgramsUseCase',
    'CreateProgramUseCase',
    'UpdateProgramUseCase',
    'DeleteProgramUseCase',
    # Stream use cases
    'GetStreamUseCase',
    'ListStreamsByProgramUseCase',
    'CreateStreamUseCase',
    'UpdateStreamUseCase',
    'DeleteStreamUseCase',
    # Course use cases
    'GetCourseUseCase',
    'GetCourseByCodeUseCase',
    'ListCoursesUseCase',
    'ListUnassignedCoursesUseCase',
    'CreateCourseUseCase',
    'UpdateCourseUseCase',
    'DeleteCourseUseCase',
    'AssignLecturerUseCase',
    'UnassignLecturerUseCase',
]
