from django.db import models
from courses.models import Course
from users.models import User

class Session(models.Model):
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    lecturer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'lecturer'},
        related_name='sessions'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # New fields
    is_active = models.BooleanField(
        default=False,
        help_text="Is attendance scanning active for this session?"
    )
    qr_code_displayed = models.CharField(
        max_length=255,
        blank=True,
        help_text="QR code displayed by lecturer (optional)"
    )
    allow_late_submission = models.BooleanField(
        default=False,
        help_text="Allow attendance after session ends?"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-start_time']
        verbose_name = 'Session'
        verbose_name_plural = 'Sessions'

    def __str__(self):
        return f"{self.course.code} - {self.date} ({self.start_time}-{self.end_time})"
    
    def activate(self):
        """Enable attendance scanning for this session"""
        self.is_active = True
        self.save()
    
    def deactivate(self):
        """Disable attendance scanning for this session"""
        self.is_active = False
        self.save()
    
    def get_attendance_count(self):
        """Get number of students who marked attendance"""
        return self.attendance_set.filter(status='present').count()
    
    def get_present_students(self):
        """Get list of students who attended"""
        return self.attendance_set.filter(status='present').select_related('student')
    
    def get_absent_students(self):
        """Get list of enrolled students who didn't attend"""
        enrolled_students = self.course.students.all()
        attended_students = self.attendance_set.filter(
            status='present'
        ).values_list('student_id', flat=True)
        return enrolled_students.exclude(id__in=attended_students)
    
    def get_attendance_percentage(self):
        """Calculate attendance percentage"""
        total_students = self.course.get_student_count()
        if total_students == 0:
            return 0
        present_count = self.get_attendance_count()
        return (present_count / total_students) * 100