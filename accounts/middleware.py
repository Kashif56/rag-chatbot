from django.shortcuts import redirect
from django.contrib import messages
from django.urls import resolve, reverse
from django.conf import settings


class EmailVerificationMiddleware:
    """
    Middleware to enforce email verification for authenticated users.
    Redirects users to the verification page if their email is not verified.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Check if user is authenticated
        if request.user.is_authenticated:
            # Get the current URL name
            url_name = resolve(request.path_info).url_name
            app_name = resolve(request.path_info).app_name
            
            # List of URLs that don't require email verification
            exempt_urls = [
                'verify_email',
                'resend_otp',
                'verification_success',
                'logout',
                'admin:index',
                'admin:login',
            ]
            
            # Check if the current URL requires verification
            if (url_name not in exempt_urls and 
                f"{app_name}:{url_name}" not in exempt_urls and
                not request.path.startswith('/admin/')):
                
                # Check if user's email is verified
                if not request.user.profile.is_email_verified:
                    messages.warning(request, 'Please verify your email to access this page.')
                    return redirect('accounts:verify_email')
        
        response = self.get_response(request)
        return response
