from django.db import models
from django.contrib.auth.models import User


class Credentials(models.Model):
    chatbot = models.ForeignKey('chat.Chatbot', on_delete=models.CASCADE)
    twilio_account_sid = models.CharField(max_length=255)
    twilio_auth_token = models.CharField(max_length=255)
    twilio_phone_number = models.CharField(max_length=255)
   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.chatbot.name

