from django.db import models
from django.contrib.auth.models import User
import uuid

# ---------- Choices ----------
LLM_PROVIDER_CHOICES = [
    ('openai', 'OpenAI'),
    ('google', 'Google'),
    ('deepseek', 'DeepSeek'),
]

LLM_MODEL_CHOICES = [
    ('gpt-4o-mini', 'GPT-4o Mini'),
    ('gpt-4o', 'GPT-4o'),
    ('gpt-4', 'GPT-4'),
    ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),
    ('gemini-1.5-pro-latest', 'Gemini 1.5 Pro'),
    ('deepseek-chat', 'DeepSeek Chat'),
]

CHANNEL_TYPE_CHOICES = [
    ('whatsapp', 'WhatsApp'),
    ('messenger', 'Messenger'),
    ('sms', 'SMS'),
    ('email', 'Email'),
    ('web', 'Web Chat'),
]

# ---------- Chatbot ----------
class Chatbot(models.Model):
    chatbot_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default="New Chatbot")
    description = models.TextField(null=True, blank=True)
    prompt = models.TextField(null=True, blank=True)

    llm_provider = models.CharField(max_length=255, choices=LLM_PROVIDER_CHOICES, default='openai')
    llm_model = models.CharField(max_length=255, choices=LLM_MODEL_CHOICES, default='gpt-4o-mini')

    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    

    def get_messages_count(self):
        messages = 0
        conversation = Conversation.objects.filter(chatbot=self)
        for chat in conversation:
            messages += chat.messages.count()
        return messages


# ---------- Channel (Base) ----------
class Channel(models.Model):
    channel_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chatbot = models.ForeignKey(Chatbot, on_delete=models.CASCADE)
    channel_type = models.CharField(max_length=255, choices=CHANNEL_TYPE_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.channel_type} - {self.chatbot.name}"

# ---------- Channel Specific Models ----------

# Email
class EmailChannel(models.Model):
    channel = models.OneToOneField(Channel, on_delete=models.CASCADE, related_name='email_config', null=True, blank=True)

    email_address = models.EmailField()
    provider = models.CharField(max_length=100, choices=[
        ("gmail", "Gmail"),
        ("outlook", "Outlook"),
        ("imap", "IMAP"),
        ("smtp", "SMTP Custom"),
    ])
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, null=True)
    smtp_server = models.CharField(max_length=255, blank=True, null=True)
    smtp_port = models.CharField(max_length=255, blank=True, null=True)
    imap_server = models.CharField(max_length=255, blank=True, null=True)
    imap_port = models.CharField(max_length=255, blank=True, null=True)
    last_synced = models.DateTimeField(null=True, blank=True)
    # Gmail API push notification fields
    watch_expiration = models.DateTimeField(null=True, blank=True)
    watch_history_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.email_address} - {self.provider}"

# WhatsApp
class WhatsAppChannel(models.Model):
    channel = models.OneToOneField(Channel, on_delete=models.CASCADE, related_name='whatsapp_config', null=True, blank=True)
    twilio_account_sid = models.CharField(max_length=255, blank=True, null=True)
    twilio_auth_token = models.CharField(max_length=255, blank=True, null=True)
    twilio_phone_number = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.twilio_phone_number}"

# Messenger
class MessengerChannel(models.Model):
    channel = models.OneToOneField(Channel, on_delete=models.CASCADE, related_name='messenger_config', null=True, blank=True)
    page_id = models.CharField(max_length=255, null=True, blank=True)
    page_name = models.CharField(max_length=255, null=True, blank=True)
    access_token = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.page_name} - {self.page_id}"


# ---------- Message & Conversation ----------
class Message(models.Model):
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey('Conversation', on_delete=models.CASCADE, related_name="messages")
    content = models.TextField(null=True, blank=True)
    role = models.CharField(max_length=255, choices=[('user', 'User'), ('assistant', 'Assistant')])

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content[:50]

class Conversation(models.Model):
    conversation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chatbot = models.ForeignKey(Chatbot, on_delete=models.CASCADE)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)

    from_number = models.CharField(max_length=255) # Identifier for SMS and WhatsApp
    from_email = models.CharField(max_length=255) # Identifier for Email


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation {self.conversation_id}"


# ---------- Email Processing ----------
class ProcessedEmail(models.Model):
    """Tracks emails that have been processed to prevent duplicate processing."""
    message_id = models.CharField(max_length=255, unique=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Processed email {self.message_id[:30]}..."
