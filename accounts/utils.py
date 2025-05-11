from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import OTPVerification
from datetime import datetime


def send_otp_email(user, otp_code):
    """
    Send OTP verification email to the user
    """
    subject = 'Verify Your Email - NexusAI'
    html_message = render_to_string('accounts/email/verification_email.html', {
        'user': user,
        'otp_code': otp_code,
    })
    plain_message = strip_tags(html_message)
    
    return send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )


def generate_otp(user):
    """
    Generate a new OTP for the user and send it via email
    """
    # Invalidate any existing OTPs
    OTPVerification.objects.filter(user=user, is_used=False).update(is_used=True)
    
    # Create a new OTP
    otp_verification = OTPVerification.objects.create(user=user)
    
    # Send OTP email
    send_otp_email(user, otp_verification.otp_code)
    
    return otp_verification


def verify_otp(user, otp_code):
    """
    Verify the OTP code provided by the user
    """
    try:
        otp_verification = OTPVerification.objects.get(
            user=user,
            otp_code=otp_code,
            is_used=False
        )
        
        # Check if OTP is expired
        if otp_verification.is_expired:
            return False, "OTP has expired. Please request a new one."
        
        # Mark OTP as used
        otp_verification.is_used = True
        otp_verification.save()
        
        # Mark user as verified
        user.profile.is_email_verified = True
        user.profile.email_verification_date = datetime.now()
        user.profile.save()
        
        return True, "Email verified successfully."
    except OTPVerification.DoesNotExist:
        return False, "Invalid OTP code. Please try again."
