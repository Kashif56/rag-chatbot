from django.db.models.signals import post_save
from django.dispatch import receiver
from chat.models import Chatbot
from kb.models import KnowledgeBase


@receiver(post_save, sender=Chatbot)
def create_email_channel(sender, instance, created, **kwargs):
    if created:
        KnowledgeBase.objects.create(chatbot=instance)