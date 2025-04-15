from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class DataSource(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.URLField(blank=True, null=True)
    file = models.FileField(upload_to='data_sources/', blank=True)
    text_title = models.CharField(max_length=200)
    text_content = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text_title


