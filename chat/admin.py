from django.contrib import admin
from .models import Chatbot, Channel, EmailChannel, WhatsAppChannel, MessengerChannel, Message, Conversation

admin.site.register(Chatbot)
admin.site.register(Channel)
admin.site.register(EmailChannel)
admin.site.register(WhatsAppChannel)
admin.site.register(MessengerChannel)
admin.site.register(Message)
admin.site.register(Conversation)
