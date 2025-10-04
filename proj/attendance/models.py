from django.db import models
from session.models import Session  # Changed from sessions
from users.models import User

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
    )
    
    SCAN_METHOD_CHOICES = (
        ('qr', 'QR Code Scan'),
        ('manual', 'Manual Entry'),
    )
    
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'student'}
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    
    scan_method = models.CharField(
        max_length=10,
        choices=SCAN_METHOD_CHOICES,
        default='qr',
        help_text="How was attendance marked?"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of device used for scanning"
    )
    verified = models.BooleanField(
        default=True,
        help_text="Is this attendance verified by lecturer?"
    )

    class Meta:
        unique_together = ('session', 'student')
        ordering = ['-timestamp']
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'

    def __str__(self):
        return f"{self.student.username} - {self.session} - {self.status}"