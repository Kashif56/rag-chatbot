from django.urls import path

from . import views
from . import channels_response_views
from . import google

app_name = 'chat'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('conversations/', views.conversations, name='conversations'),
    path('conversation/<uuid:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('create-chatbot/', views.create_chatbot_page, name='create_chatbot_page'),
    path('add-chatbot/', views.add_chatbot, name='add_chatbot'),
    path('chatbot/<str:chatbot_id>/', views.edit_chatbot_page, name='edit_chatbot_page'),
    path('update-chatbot/<str:chatbot_id>/', views.update_chatbot, name='update_chatbot'),
    path('add-channel/<str:chatbot_id>/', views.add_channel, name='add_channel'),
    path('update-channel/<str:channel_id>/', views.update_channel, name='update_channel'),
    path('delete-channel/<str:channel_id>/', views.delete_channel, name='delete_channel'),
    # Public conversation routes
    path('chat/<str:chatbot_id>/', views.public_conversation, name='public_conversation'),
    path('api/chat/', views.chat_api, name='chat_api'),
    
    # Twilio webhook endpoints
    path('api/webhook/sms/<str:chatbot_id>/', channels_response_views.handle_sms, name='handle_sms'),
    path('api/webhook/whatsapp/<str:chatbot_id>/', channels_response_views.handle_whatsapp, name='handle_whatsapp'),
    
    # Gmail OAuth and Pub/Sub webhook endpoints
    path('google/auth/<uuid:channel_id>/', views.gmail_auth, name='gmail_auth'),
    path('google/oauth2callback/', google.oauth2callback, name='gmail_oauth2callback'),
    path('webhook/gmail/', google.gmail_push_notification, name='gmail_push_notification'),
    path('google/stop-watch/', google.stop_gmail_watch, name='stop_gmail_watch'),
]