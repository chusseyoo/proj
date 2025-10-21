from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from .models import Attendance
from session.models import Session
from users.models import User
import json

# View 1: Display QR Scanner Page (Public - no login required)
def scan_attendance_view(request, session_id):
    """
    Public page where students scan their QR codes
    No authentication needed - students don't login
    """
    session = get_object_or_404(Session, id=session_id)
    
    # Check if session is active
    if not session.is_active:
        return render(request, 'attendance/scan_error.html', {
            'error': 'This session is not currently accepting attendance.'
        })
    
    return render(request, 'attendance/scan.html', {
        'session': session
    })


# View 2: Verify QR Code and Record Attendance (AJAX endpoint)
@csrf_exempt  # Or use proper CSRF token handling
def verify_qr_view(request):
    """
    CRITICAL: This is where you restrict to students only
    Receives scanned QR code data and validates it
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        qr_code_data = data.get('qr_code')
        session_id = data.get('session_id')
        
        if not qr_code_data or not session_id:
            return JsonResponse({'error': 'Missing data'}, status=400)
        
        # Get the session
        session = Session.objects.get(id=session_id)
        
        # Check if session is active
        if not session.is_active:
            return JsonResponse({
                'success': False,
                'error': 'Session is not active'
            }, status=400)
        
        # Find user by QR code
        try:
            user = User.objects.get(qr_code=qr_code_data)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid QR code'
            }, status=404)

        # CRITICAL CHECK: Only students can mark attendance
        if user.role != 'student':
            return JsonResponse({
                'success': False,
                'error': 'Only students can mark attendance using QR codes'
            }, status=403)
        
        # Check if student is enrolled in the course
        if not user.enrolled_courses.filter(id=session.course.id).exists():
            return JsonResponse({
                'success': False,
                'error': 'You are not enrolled in this course'
            }, status=403)
        
        # Check for duplicate attendance
        if Attendance.objects.filter(session=session, student=user).exists():
            return JsonResponse({
                'success': False,
                'error': 'Attendance already marked for this session'
            }, status=400)
        
        # Record attendance
        attendance = Attendance.objects.create(
            session=session,
            student=user,
            status='present',
            scan_method='qr',
            ip_address=get_client_ip(request)
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Attendance marked for {user.get_full_name() or user.username}',
            'student_name': user.get_full_name() or user.username,
            'timestamp': attendance.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Session.DoesNotExist:
        return JsonResponse({'error': 'Session not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_client_ip(request):
    """Helper function to get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# View 3: Manual Attendance (Lecturer only)


@login_required
def manual_attendance_view(request, session_id):
    """
    Lecturers can manually mark attendance
    This is backup - no QR scanning involved
    """
    # Check if user is lecturer
    if request.user.role != 'lecturer':
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    session = get_object_or_404(Session, id=session_id)
    
    # Check if lecturer owns this session
    if session.lecturer != request.user:
        return JsonResponse({'error': 'You cannot mark attendance for this session'}, status=403)
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        status = request.POST.get('status', 'present')
        
        try:
            student = User.objects.get(id=student_id, role='student')
            
            # Create or update attendance
            attendance, created = Attendance.objects.update_or_create(
                session=session,
                student=student,
                defaults={
                    'status': status,
                    'scan_method': 'manual'
                }
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Attendance marked for {student.username}'
            })
            
        except User.DoesNotExist:
            return JsonResponse({'error': 'Student not found'}, status=404)
    
    # GET request - show form
    enrolled_students = session.course.students.all()
    
    return render(request, 'attendance/manual_attendance.html', {
        'session': session,
        'students': enrolled_students
    })