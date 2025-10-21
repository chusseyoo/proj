"""
Application-level use cases orchestrating services according to proj_docs.

Each use case provides a small, focused handler that composes services
and returns plain dicts or domain objects as appropriate.
"""

from .auth_use_cases import (
	LoginUseCase,
	RefreshAccessTokenUseCase,
	GenerateStudentAttendanceTokenUseCase,
)
from .registration_use_cases import (
	RegisterLecturerUseCase,
	RegisterStudentUseCase,
	RegisterAdminUseCase,
)
from .user_use_cases import (
	GetUserByIdUseCase,
	GetUserByEmailUseCase,
	UpdateUserUseCase,
	ActivateUserUseCase,
	DeactivateUserUseCase,
)
from .profile_use_cases import (
	GetStudentProfileUseCase,
	GetStudentProfileByUserIdUseCase,
	GetStudentProfileByStudentIdUseCase,
	UpdateStudentProfileUseCase,
	GetLecturerProfileUseCase,
	GetLecturerProfileByUserIdUseCase,
	UpdateLecturerProfileUseCase,
)

__all__ = [
	# Auth
	"LoginUseCase",
	"RefreshAccessTokenUseCase",
	"GenerateStudentAttendanceTokenUseCase",
	# Registration
	"RegisterLecturerUseCase",
	"RegisterStudentUseCase",
	"RegisterAdminUseCase",
	# Users
	"GetUserByIdUseCase",
	"GetUserByEmailUseCase",
	"UpdateUserUseCase",
	"ActivateUserUseCase",
	"DeactivateUserUseCase",
	# Profiles
	"GetStudentProfileUseCase",
	"GetStudentProfileByUserIdUseCase",
	"GetStudentProfileByStudentIdUseCase",
	"UpdateStudentProfileUseCase",
	"GetLecturerProfileUseCase",
	"GetLecturerProfileByUserIdUseCase",
	"UpdateLecturerProfileUseCase",
]

