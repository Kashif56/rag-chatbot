from django.shortcuts import render

def handler400(request, exception=None):
    """
    Handle 400 Bad Request errors
    """
    context = {
        'status_code': 400,
        'error_title': 'Bad Request',
        'error_message': 'Sorry, the request could not be processed due to invalid syntax. Please check your input and try again.'
    }
    return render(request, 'errors/400.html', context, status=400)

def handler401(request, exception=None):
    """
    Handle 401 Unauthorized errors
    """
    context = {
        'status_code': 401,
        'error_title': 'Authentication Required',
        'error_message': 'You need to be logged in to access this page. Please sign in with your account credentials.'
    }
    return render(request, 'errors/401.html', context, status=401)

def handler403(request, exception=None):
    """
    Handle 403 Forbidden errors
    """
    context = {
        'status_code': 403,
        'error_title': 'Access Denied',
        'error_message': 'Sorry, you don\'t have permission to access this page. Please check your credentials or contact support if you believe this is an error.'
    }
    return render(request, 'errors/403.html', context, status=403)

def handler404(request, exception=None):
    """
    Handle 404 Not Found errors
    """
    context = {
        'status_code': 404,
        'error_title': 'Page Not Found',
        'error_message': 'The page you\'re looking for doesn\'t exist or has been moved.'
    }
    return render(request, 'errors/404.html', context, status=404)

def handler500(request, exception=None):
    """
    Handle 500 Server Error
    """
    context = {
        'status_code': 500,
        'error_title': 'Server Error',
        'error_message': 'Sorry, something went wrong on our end. Our team has been notified and we\'re working to fix the issue.'
    }
    return render(request, 'errors/500.html', context, status=500)

def custom_error_view(request, status_code, error_title=None, error_message=None):
    """
    Generic error handler for any other HTTP error codes
    """
    context = {
        'status_code': status_code,
        'error_title': error_title or f'Error {status_code}',
        'error_message': error_message or 'Sorry, an error occurred. Please try again later or contact support if the problem persists.'
    }
    return render(request, 'errors/generic.html', context, status=status_code)
