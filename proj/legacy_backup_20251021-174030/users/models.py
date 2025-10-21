from django.db import models
from django.contrib.auth.models import AbstractUser
import secrets
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('lecturer', 'Lecturer'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    
    # STRING: Unique token stored in database (what gets encoded in QR)
    qr_code = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        unique=True,
        help_text="Unique token encoded in student's QR code"
    )
    
    # IMAGE: Actual QR code image file
    qr_code_image = models.ImageField(
        upload_to='qr_codes/',
        blank=True,
        null=True,
        help_text="Generated QR code image"
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def generate_qr_code(self):
        """
        Generate unique QR code token and image for student
        Only runs for students
        """
        if self.role != 'student':
            return
        
        # Step 1: Generate unique token (if not exists)
        if not self.qr_code:
            # Format: STUDENT_<ID>_<RANDOM_TOKEN>
            random_token = secrets.token_urlsafe(16)
            self.qr_code = f"STUDENT_{self.id}_{random_token}"
        
        # Step 2: Create QR code image from the token
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # Add the token string to QR code
        qr.add_data(self.qr_code)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Step 3: Save image to ImageField
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        file_name = f'qr_{self.username}_{self.id}.png'
        self.qr_code_image.save(file_name, File(buffer), save=False)
        buffer.close()
    
    def save(self, *args, **kwargs):
        """
        Override save to auto-generate QR code for new students
        """
        # Save first to get ID (needed for QR token)
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Generate QR code for new students
        if is_new and self.role == 'student':
            self.generate_qr_code()
            super().save(update_fields=['qr_code', 'qr_code_image'])


# Example of what gets stored:
# 
# User ID: 123
# username: "john_doe"
# role: "student"
# qr_code: "STUDENT_123_TOKEN_a1b2c3d4e5f6g7h8"  ← Stored in database (TEXT)
# qr_code_image: "qr_codes/qr_john_doe_123.png"  ← Stored as file (IMAGE)
#
# When John scans his QR code with phone camera:
# Camera reads: "STUDENT_123_TOKEN_a1b2c3d4e5f6g7h8"
# System searches database for this string
# Finds User ID 123 (John)
# Records attendance for John