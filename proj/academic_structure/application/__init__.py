"""Application layer for academic structure domain."""

# Import DTOs
from .dto import (
    ProgramDTO,
    StreamDTO,
    CourseDTO,
    to_program_dto,
    to_stream_dto,
    to_course_dto,
)

# Import use cases
from .use_cases import (
    # Program use cases
    GetProgramUseCase,
    GetProgramByCodeUseCase,
    ListProgramsUseCase,
    CreateProgramUseCase,
    UpdateProgramUseCase,
    DeleteProgramUseCase,
    # Stream use cases
    GetStreamUseCase,
    ListStreamsByProgramUseCase,
    CreateStreamUseCase,
    UpdateStreamUseCase,
    DeleteStreamUseCase,
    # Course use cases
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
    # DTOs
    'ProgramDTO',
    'StreamDTO',
    'CourseDTO',
    'to_program_dto',
    'to_stream_dto',
    'to_course_dto',
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
