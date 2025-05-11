from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import random
import string
from datetime import datetime, timedelta


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_email_verified = models.BooleanField(default=False)
    email_verification_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class OTPVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.otp_code}"
    
    def save(self, *args, **kwargs):
        if not self.otp_code:
            # Generate a random 6-digit OTP code
            self.otp_code = ''.join(random.choices(string.digits, k=6))
        
        if not self.expires_at:
            # Set expiration to 10 minutes from now
            from django.utils import timezone
            self.expires_at = timezone.now() + timedelta(minutes=10)
            
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at


class Credentials(models.Model):
    chatbot = models.ForeignKey('chat.Chatbot', on_delete=models.CASCADE)
    twilio_account_sid = models.CharField(max_length=255)
    twilio_auth_token = models.CharField(max_length=255)
    twilio_phone_number = models.CharField(max_length=255)
   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.chatbot.name

