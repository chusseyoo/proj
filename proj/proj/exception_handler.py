"""
Global exception handler for chaining context-specific exception handlers.

This handler allows each bounded context to handle its own exceptions
while maintaining separation of concerns.
"""


def global_exception_handler(exc, context):
    """
    Global exception handler that chains context-specific handlers.
    
    Each bounded context can have its own exception handler that maps
    domain exceptions to HTTP responses. This global handler tries each
    context-specific handler in order until one returns a response.
    
    Args:
        exc: The exception that was raised
        context: The context in which the exception occurred
        
    Returns:
        Response object or None
    """
    # Try academic_structure handler
    try:
        from academic_structure.interfaces.api.exceptions import custom_exception_handler as academic_structure_handler
        response = academic_structure_handler(exc, context)
        if response is not None:
            return response
    except ImportError:
        pass
    
    # Try user_management handler
    try:
        from user_management.interfaces.api.exceptions import custom_exception_handler as user_management_handler
        response = user_management_handler(exc, context)
        if response is not None:
            return response
    except ImportError:
        pass
    
    # Add more context handlers here as needed
    # try:
    #     from other_context.interfaces.api.exceptions import custom_exception_handler as other_handler
    #     response = other_handler(exc, context)
    #     if response is not None:
    #         return response
    # except ImportError:
    #     pass
    
    # Fallback to DRF's default exception handler
    # Import here to avoid circular imports at module load time
    from rest_framework.views import exception_handler as drf_exception_handler
    return drf_exception_handler(exc, context)
