from django.urls import path
from . import views

app_name = 'kb'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create-chatbot/', views.create_chatbot_page, name='create_chatbot_page'),
    path('chatbot/<int:chatbot_id>/', views.edit_chatbot_page, name='edit_chatbot_page'),

]

