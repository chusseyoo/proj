from django.db import models
from users.models import User

class Course(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, help_text="Course description")
    lecturer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'lecturer'},
        related_name='taught_courses'
    )
    
    # Students enrolled in this course
    students = models.ManyToManyField(
        User,
        limit_choices_to={'role': 'student'},
        related_name='enrolled_courses',
        blank=True,
        help_text="Students enrolled in this course"
    )
    
    is_active = models.BooleanField(default=True, help_text="Is this course active?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'

    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_enrolled_students(self):
        """Get all students enrolled in this course"""
        return self.students.filter(role='student')
    
    def get_student_count(self):
        """Get count of enrolled students"""
        return self.students.count()
    
    def enroll_student(self, student):
        """Enroll a student in this course"""
        if student.role == 'student':
            self.students.add(student)
            return True
        return False
    
    def unenroll_student(self, student):
        """Remove a student from this course"""
        self.students.remove(student)