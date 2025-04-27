from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Dashboard pages
    path('', views.analytics_dashboard, name='analytics_dashboard'),
    path('chatbot/<str:chatbot_id>/', views.chatbot_analytics, name='chatbot_analytics'),
    
    # API endpoints for KPIs
    path('api/total-messages/', views.get_total_messages, name='api_total_messages'),
    path('api/unique-users/', views.get_unique_users, name='api_unique_users'),
    path('api/active-chatbots/', views.get_active_chatbots, name='api_active_chatbots'),
    path('api/avg-response-time/', views.get_avg_response_time, name='api_avg_response_time'),
    
    # API endpoints for charts
    path('api/message-volume/', views.get_message_volume_data, name='api_message_volume'),
    path('api/user-engagement/', views.get_user_engagement_data, name='api_user_engagement'),
    path('api/channel-distribution/', views.get_channel_distribution_data, name='api_channel_distribution'),
    
    # API endpoints for other dashboard components
    path('api/chatbot-performance/', views.get_chatbot_performance_data, name='api_chatbot_performance'),
    path('api/recent-activity/', views.get_recent_activity_data, name='api_recent_activity'),
]