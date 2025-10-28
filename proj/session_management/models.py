from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Session(models.Model):
	"""Session model aligned to proj_docs session-management spec.

	Fields and constraints follow `models_guide.md` in proj_docs:
	- session_id: PK
	- program: FK -> academic_structure.Program
	- course: FK -> academic_structure.Course
	- lecturer: FK -> user_management.LecturerProfile (PROTECT)
	- stream: FK -> academic_structure.Stream (nullable)
	- date_created: Date (auto)
	- time_created: DateTime (session start)
	- time_ended: DateTime (session end)
	- latitude/longitude: captured at creation (precision matching docs)
	- location_description: optional text
	"""

	session_id = models.AutoField(primary_key=True)
	program = models.ForeignKey(
		"academic_structure.Program",
		on_delete=models.CASCADE,
		related_name="sessions",
	)
	course = models.ForeignKey(
		"academic_structure.Course",
		on_delete=models.CASCADE,
		related_name="sessions",
	)
	lecturer = models.ForeignKey(
		"user_management.LecturerProfile",
		on_delete=models.PROTECT,
		related_name="sessions",
	)
	stream = models.ForeignKey(
		"academic_structure.Stream",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="sessions",
	)

	# Creation timestamp/date
	date_created = models.DateField(auto_now_add=True)
	time_created = models.DateTimeField()
	time_ended = models.DateTimeField()

	# Location captured at creation; docs prefer high precision
	latitude = models.DecimalField(
		max_digits=10, decimal_places=8,
	)
	longitude = models.DecimalField(
		max_digits=11, decimal_places=8,
	)
	location_description = models.CharField(max_length=100, null=True, blank=True)

	class Meta:
		db_table = "sessions"
		indexes = [
			models.Index(fields=["course"], name="idx_sessions_course_id"),
			models.Index(fields=["lecturer"], name="idx_sessions_lecturer_id"),
			models.Index(fields=["program", "stream"], name="idx_sessions_program_stream"),
			models.Index(fields=["time_created", "time_ended"], name="idx_sessions_time"),
		]
		constraints = [
			models.CheckConstraint(check=models.Q(time_ended__gt=models.F("time_created")), name="ck_time_window_valid"),
			models.CheckConstraint(check=models.Q(latitude__gte=-90) & models.Q(latitude__lte=90), name="ck_lat_range"),
			models.CheckConstraint(check=models.Q(longitude__gte=-180) & models.Q(longitude__lte=180), name="ck_lon_range"),
		]

	def __str__(self) -> str:  # pragma: no cover - trivial
		return f"Session {self.session_id} (course={self.course}, lecturer={self.lecturer})" 

