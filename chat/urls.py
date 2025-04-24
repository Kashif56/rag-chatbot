from django.urls import path

from . import views

app_name = 'chat'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
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
]