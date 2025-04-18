from django.db import models
from django.contrib.auth.models import User
import uuid


SOURCE_TYPE_CHOICES = [
    ('url', 'URL'),
    ('file', 'File'),
    ('text', 'Text'),
]

class DataSource(models.Model):
    kb = models.ForeignKey('KnowledgeBase', on_delete=models.CASCADE)
    url = models.URLField(blank=True, null=True)
    file = models.FileField(upload_to='data_sources/', blank=True)
    text_title = models.CharField(max_length=200)
    text_content = models.TextField()
    source_type = models.CharField(max_length=200, choices=SOURCE_TYPE_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text_title



class KnowledgeBase(models.Model):
    knowledge_base_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chatbot = models.ForeignKey('chat.Chatbot', on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
