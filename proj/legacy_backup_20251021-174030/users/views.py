from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import User
import json


# ============================================
# AUTHENTICATION VIEWS
# ============================================

@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    """
    Login view for Admin and Lecturer only
    
    POST data:
        - username: str
        - password: str
    
    Returns:
        JSON response with success/error
    """
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({
                'success': False,
                'error': 'Username and password are required'
            }, status=400)
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user is admin or lecturer
            if user.role not in ['admin', 'lecturer']:
                return JsonResponse({
                    'success': False,
                    'error': 'Only admin and lecturers can login'
                }, status=403)
            
            # Login user
            login(request, user)
            
            return JsonResponse({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'full_name': user.get_full_name() or user.username
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid username or password'
            }, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def logout_view(request):
    """
    Logout current user
    
    Returns:
        JSON response
    """
    logout(request)
    return JsonResponse({
        'success': True,
        'message': 'Logged out successfully'
    })


@login_required
def current_user_view(request):
    """
    Get current logged in user details
    
    Returns:
        JSON response with user data
    """
    user = request.user
    return JsonResponse({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'full_name': user.get_full_name() or user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
    })


# ============================================
# USER MANAGEMENT VIEWS (Admin only)
# ============================================

@login_required
@require_http_methods(["POST"])
def create_user_view(request):
    """
    Create a new user (Admin only)
    
    POST data:
        - username: str
        - email: str
        - password: str
        - role: str (admin/lecturer/student)
        - first_name: str (optional)
        - last_name: str (optional)
    
    Returns:
        JSON response with created user data
    """
    # Check if user is admin
    if request.user.role != 'admin':
        return JsonResponse({
            'success': False,
            'error': 'Permission denied. Only admins can create users.'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        # Validation
        if not all([username, email, password, role]):
            return JsonResponse({
                'success': False,
                'error': 'Username, email, password, and role are required'
            }, status=400)
        
        if role not in ['admin', 'lecturer', 'student']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid role. Must be admin, lecturer, or student'
            }, status=400)
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'success': False,
                'error': 'Username already exists'
            }, status=400)
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            first_name=first_name,
            last_name=last_name
        )
        
        return JsonResponse({
            'success': True,
            'message': f'User {username} created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'full_name': user.get_full_name() or user.username,
                'qr_code': user.qr_code if role == 'student' else None
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def list_users_view(request):
    """
    List all users (Admin only)
    Optional query params:
        - role: filter by role
        - search: search by username or email
    
    Returns:
        JSON response with list of users
    """
    # Check if user is admin
    if request.user.role != 'admin':
        return JsonResponse({
            'success': False,
            'error': 'Permission denied. Only admins can view all users.'
        }, status=403)
    
    # Get query params
    role = request.GET.get('role')
    search = request.GET.get('search')
    
    # Base query
    users = User.objects.all()
    
    # Apply filters
    if role:
        users = users.filter(role=role)
    
    if search:
        users = users.filter(
            username__icontains=search
        ) | users.filter(
            email__icontains=search
        )
    
    # Serialize users
    users_data = [{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'full_name': user.get_full_name() or user.username,
        'is_active': user.is_active,
        'qr_code': user.qr_code if user.role == 'student' else None
    } for user in users]
    
    return JsonResponse({
        'success': True,
        'count': len(users_data),
        'users': users_data
    })


@login_required
def user_detail_view(request, user_id):
    """
    Get details of a specific user
    
    Returns:
        JSON response with user details
    """
    # Admin can view any user, lecturers can only view themselves
    if request.user.role not in ['admin', 'lecturer']:
        return JsonResponse({
            'success': False,
            'error': 'Permission denied'
        }, status=403)
    
    # Lecturers can only view their own profile
    if request.user.role == 'lecturer' and request.user.id != user_id:
        return JsonResponse({
            'success': False,
            'error': 'You can only view your own profile'
        }, status=403)
    
    user = get_object_or_404(User, id=user_id)
    
    return JsonResponse({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'full_name': user.get_full_name() or user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': user.is_active,
            'date_joined': user.date_joined.isoformat(),
            'qr_code': user.qr_code if user.role == 'student' else None,
            'qr_code_image': user.qr_code_image.url if user.role == 'student' and user.qr_code_image else None
        }
    })


@login_required
@require_http_methods(["PUT", "PATCH"])
def update_user_view(request, user_id):
    """
    Update user details (Admin only)
    
    PUT/PATCH data:
        - email: str (optional)
        - first_name: str (optional)
        - last_name: str (optional)
        - is_active: bool (optional)
    
    Returns:
        JSON response
    """
    # Check if user is admin
    if request.user.role != 'admin':
        return JsonResponse({
            'success': False,
            'error': 'Permission denied. Only admins can update users.'
        }, status=403)
    
    user = get_object_or_404(User, id=user_id)
    
    try:
        data = json.loads(request.body)
        
        # Update fields if provided
        if 'email' in data:
            user.email = data['email']
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'full_name': user.get_full_name() or user.username,
                'is_active': user.is_active
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_user_view(request, user_id):
    """
    Delete a user (Admin only)
    
    Returns:
        JSON response
    """
    # Check if user is admin
    if request.user.role != 'admin':
        return JsonResponse({
            'success': False,
            'error': 'Permission denied. Only admins can delete users.'
        }, status=403)
    
    user = get_object_or_404(User, id=user_id)
    
    # Prevent deleting self
    if user.id == request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'You cannot delete your own account'
        }, status=400)
    
    username = user.username
    user.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'User {username} deleted successfully'
    })