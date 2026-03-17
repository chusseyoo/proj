from django.contrib import admin
from django import forms

from .infrastructure.orm.django_models import (
	User,
	StudentProfile,
	LecturerProfile,
)


class StudentProfileAdminForm(forms.ModelForm):
	student_email = forms.EmailField(label="Email", required=True)

	class Meta:
		model = StudentProfile
		exclude = ("user",)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self.instance and self.instance.pk and self.instance.user:
			self.fields["student_email"].initial = self.instance.user.email

	def clean_student_email(self):
		email = self.cleaned_data["student_email"].strip().lower()
		return email

	def clean(self):
		cleaned_data = super().clean()
		email = cleaned_data.get("student_email")
		if not email:
			return cleaned_data

		try:
			user = User.objects.get(email=email)
			if user.role != User.Roles.STUDENT:
				raise forms.ValidationError("This email belongs to a non-student user.")

			existing_profile = StudentProfile.objects.filter(user=user)
			if self.instance and self.instance.pk:
				existing_profile = existing_profile.exclude(pk=self.instance.pk)
			if existing_profile.exists():
				raise forms.ValidationError("A student profile already exists for this email.")
		except User.DoesNotExist:
			# Create a student user when email does not exist yet.
			user = User.objects.create_user(
				email=email,
				role=User.Roles.STUDENT,
				first_name="Student",
				last_name="User",
			)

		self.instance.user = user
		return cleaned_data


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
	list_display = ("user_id", "email", "first_name", "last_name", "role", "is_active")
	list_filter = ("role", "is_active")
	search_fields = ("email", "first_name", "last_name")
	ordering = ("email",)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
	form = StudentProfileAdminForm
	list_display = ("student_profile_id", "student_id", "user", "program", "stream", "year_of_study")
	search_fields = ("student_id", "user__email", "user__first_name", "user__last_name")
	list_filter = ("program", "stream", "year_of_study")
	fields = ("student_email", "student_id", "program", "stream", "year_of_study", "qr_code_data")


@admin.register(LecturerProfile)
class LecturerProfileAdmin(admin.ModelAdmin):
	list_display = ("lecturer_id", "user", "department_name")
	search_fields = ("user__email", "user__first_name", "user__last_name", "department_name")
