from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class UserManager(BaseUserManager):
    """Custom manager for User model."""

    def create_user(self, email, role, first_name, last_name, password=None, **extra_fields):
        """Create and return a regular user."""
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email).lower()
        
        user = self.model(
            email=email,
            role=role,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser (Admin role)."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'Admin')
        extra_fields.setdefault('first_name', 'Admin')
        extra_fields.setdefault('last_name', 'User')

        if not password:
            raise ValueError("Superuser must have a password")

        return self.create_user(email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Core user entity for Admin, Lecturer, and Student.

    Notes:
    - Password is NULL for Students (passwordless auth via tokens)
    - Password is REQUIRED for Admin and Lecturer
    - Email is unique and stored lowercase
    """

    class Roles(models.TextChoices):
        ADMIN = "Admin", "Admin"
        LECTURER = "Lecturer", "Lecturer"
        STUDENT = "Student", "Student"

    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=255, unique=True, db_index=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    role = models.CharField(max_length=20, choices=Roles.choices)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Required for admin access
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']

    class Meta:
        db_table = "users"
        ordering = ["email"]
        indexes = [
            models.Index(fields=["email"], name="idx_users_email"),
            models.Index(fields=["role"], name="idx_users_role"),
        ]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.first_name} {self.last_name} ({self.email})"

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self) -> str:
        return self.get_full_name()

    def is_student(self) -> bool:
        return self.role == self.Roles.STUDENT

    def is_lecturer(self) -> bool:
        return self.role == self.Roles.LECTURER

    def is_admin(self) -> bool:
        return self.role == self.Roles.ADMIN

    def has_password(self) -> bool:
        return self.has_usable_password()

    def clean(self) -> None:
        # Normalize email to lowercase
        if self.email:
            self.email = self.email.lower()

        # Role/password business rules
        if self.role == self.Roles.STUDENT:
            # Students must not have a usable password
            if self.has_usable_password():
                raise ValidationError({
                    "password": "Students must not have a password (use passwordless auth).",
                })
        elif self.role in {self.Roles.ADMIN, self.Roles.LECTURER}:
            # Admin and Lecturer must have a password
            if not self.has_usable_password():
                raise ValidationError({
                    "password": "Admin/Lecturer must have a password.",
                })

    def save(self, *args, **kwargs):  # pragma: no cover - delegates to clean
        # For students, ensure unusable password
        if self.role == self.Roles.STUDENT and not self.pk:
            self.set_unusable_password()
        
        self.full_clean()
        return super().save(*args, **kwargs)


# --- Validators ---
import re


def validate_student_id_format(value: str) -> None:
    pattern = r"^[A-Z]{3}/[0-9]{6}$"
    if not re.match(pattern, value or ""):
        raise ValidationError("Student ID must follow format: ABC/123456")


class StudentProfile(models.Model):
    """Extended profile for students (one-to-one with User)."""

    student_profile_id = models.AutoField(primary_key=True)
    student_id = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_student_id_format],
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    program = models.ForeignKey(
        "academic_structure.Program",
        on_delete=models.PROTECT,
        related_name="students",
    )
    stream = models.ForeignKey(
        "academic_structure.Stream",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )
    year_of_study = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    qr_code_data = models.CharField(max_length=20)

    class Meta:
        db_table = "student_profiles"
        ordering = ["student_id"]
        indexes = [
            models.Index(fields=["student_id"], name="idx_student_id"),
            models.Index(fields=["user"], name="idx_student_user"),
            models.Index(fields=["program", "stream"], name="idx_prog_stream"),
        ]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.student_id} - {self.user.get_full_name()}"

    def get_program_code(self) -> str:
        return (self.student_id or "")[:3]

    def clean(self) -> None:
        # Enforce uppercase student_id and qr match in save()
        # Validate user role
        if self.user and self.user.role != User.Roles.STUDENT:
            raise ValidationError({"user": "User must have Student role"})
        # QR must equal student_id
        if self.qr_code_data and self.student_id and self.qr_code_data != self.student_id:
            raise ValidationError({
                "qr_code_data": "QR code data must match student ID",
            })
        # Stream validation depends on program.has_streams; defer to service layer

    def save(self, *args, **kwargs):  # pragma: no cover
        if self.student_id:
            self.student_id = self.student_id.upper()
        if not self.qr_code_data and self.student_id:
            self.qr_code_data = self.student_id
        self.full_clean()
        return super().save(*args, **kwargs)


class LecturerProfile(models.Model):
    """Extended profile for lecturers (one-to-one with User)."""

    lecturer_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="lecturer_profile",
    )
    department_name = models.CharField(max_length=100)

    class Meta:
        db_table = "lecturer_profiles"
        ordering = ["department_name"]
        indexes = [
            models.Index(fields=["user"], name="idx_lecturer_user"),
        ]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.user.get_full_name()} - {self.department_name}"

    def clean(self) -> None:
        if self.user and self.user.role != User.Roles.LECTURER:
            raise ValidationError({"user": "User must have Lecturer role"})
