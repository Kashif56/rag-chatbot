from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.utils import timezone

from .models import UserProfile, OTPVerification
from .utils import generate_otp, verify_otp

# Create your views here.


def signup(request):
    redirect_url = request.GET.get('next')
    if request.user.is_authenticated:
        if redirect_url:
            return redirect(redirect_url)
        else:
            redirect_url = request.META.get('HTTP_REFERER')
            return redirect(redirect_url)   
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password == password2:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username is already taken')
                return redirect('accounts:signup')
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email is already taken')
                return redirect('accounts:signup')
            
            # Create user but don't log them in yet
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            
            # Generate and send OTP
            generate_otp(user)
            
            # Store redirect URL in session if provided
            if redirect_url:
                request.session['redirect_after_verification'] = redirect_url
                
            messages.success(request, 'Account created! Please check your email for the verification code.')
            return redirect('accounts:verify_email')
        else:
            messages.error(request, 'Passwords do not match')
            return redirect('accounts:signup')

    return render(request, 'accounts/signup.html')



def login_page(request):
    redirect_url = request.GET.get('next')
    if request.user.is_authenticated:
        if redirect_url:
            return redirect(redirect_url)
        else:
            redirect_url = request.META.get('HTTP_REFERER')
            return redirect(redirect_url)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            
            if not user.profile.is_email_verified:
                messages.error(request, 'Please verify your email before logging in.')
                # Generate a new OTP for the user
                generate_otp(user)
                return redirect('accounts:verify_email')
                
            login(request, user)
            messages.success(request, 'You have been logged in successfully')
            if redirect_url:
                return redirect(redirect_url)
            else:
                return redirect('chat:dashboard')
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('accounts:login')
        
    return render(request, 'accounts/login.html')
    

@login_required
def logout_page(request):
    redirect_url = request.GET.get('next')
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    if redirect_url:
        return redirect(redirect_url)
    else:
        return redirect('core:index')


@never_cache
def verify_email(request):
    # If user is already logged in and verified, redirect to dashboard
    if request.user.is_authenticated and request.user.profile.is_email_verified:
        return redirect('chat:dashboard')
        
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        
        # If user is logged in, use that user
        if request.user.is_authenticated:
            user = request.user
        else:
            # Try to get the most recent unverified user
            try:
                latest_otp = OTPVerification.objects.filter(is_used=False).order_by('-created_at').first()
                if latest_otp:
                    user = latest_otp.user
                else:
                    messages.error(request, 'Verification session expired. Please log in again.')
                    return redirect('accounts:login')
            except Exception:
                messages.error(request, 'Verification session expired. Please log in again.')
                return redirect('accounts:login')
        
        # Verify OTP
        is_valid, message = verify_otp(user, otp_code)
        
        if is_valid:
            # Log the user in
            login(request, user)
            messages.success(request, 'Email verified successfully!')
            
            # Check if there's a redirect URL stored in session
            redirect_url = request.session.get('redirect_after_verification')
            if redirect_url:
                del request.session['redirect_after_verification']
                return redirect(redirect_url)
            else:
                return redirect('accounts:verification_success')
        else:
            messages.error(request, message)
            return redirect('accounts:verify_email')
    
    return render(request, 'accounts/verify_email.html')


@never_cache
def resend_otp(request):
    # If user is already logged in, use that user
    if request.user.is_authenticated:
        user = request.user
        generate_otp(user)
        messages.success(request, 'A new verification code has been sent to your email.')
    else:
        # Try to get the most recent unverified user
        try:
            latest_otp = OTPVerification.objects.filter(is_used=False).order_by('-created_at').first()
            if latest_otp:
                user = latest_otp.user
                generate_otp(user)
                messages.success(request, 'A new verification code has been sent to your email.')
            else:
                messages.error(request, 'Verification session expired. Please log in again.')
                return redirect('accounts:login')
        except Exception:
            messages.error(request, 'Verification session expired. Please log in again.')
            return redirect('accounts:login')
    
    return redirect('accounts:verify_email')


@login_required
def verification_success(request):
    # Only show this page to verified users
    if not request.user.profile.is_email_verified:
        return redirect('accounts:verify_email')
        
    return render(request, 'accounts/verification_success.html')


class EmailVerificationRequiredMixin:
    """Mixin to require email verification for views"""
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        # Check if user's email is verified
        if not request.user.profile.is_email_verified:
            messages.error(request, 'Please verify your email to access this page.')
            return redirect('accounts:verify_email')
        return super().dispatch(request, *args, **kwargs)
