from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Count, Avg, F, ExpressionWrapper, FloatField, Q
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from django.utils import timezone
from datetime import timedelta
import random

from chat.models import Chatbot, Channel, Message, Conversation
from kb.models import KnowledgeBase, DataSource


def analytics_dashboard(request):
    # Get summary metrics for the dashboard
    total_messages = Message.objects.count()
    unique_users = Conversation.objects.values('from_number').distinct().count()
    active_chatbots = Chatbot.objects.filter(is_active=True).count()
    
    # Calculate average response time (in seconds)
    # This is a placeholder calculation - adjust based on your actual model structure
    avg_response_time = 1  # Default fallback value
    
    context = {
        'total_messages': total_messages,
        'unique_users': unique_users,
        'active_chatbots': active_chatbots,
        'avg_response_time': avg_response_time
    }
    
    return render(request, 'analytics/analytics_dashboard.html', context)


def chatbot_analytics(request, chatbot_id):
    # Get the chatbot or return 404 if not found
    chatbot = get_object_or_404(Chatbot, id=chatbot_id)
    
    context = {
        'chatbot': chatbot
    }
    
    return render(request, 'analytics/chatbot_analytics.html', context)


# API Endpoints for Analytics Dashboard KPIs

def get_total_messages(request):
    """API endpoint to get the total number of messages"""
    time_period = request.GET.get('period', 'all')
    
    # Base query
    query = Message.objects.all()
    
    # Filter by time period
    if time_period != 'all':
        now = timezone.now()
        if time_period == 'today':
            query = query.filter(created_at__date=now.date())
        elif time_period == 'week':
            query = query.filter(created_at__gte=now - timedelta(days=7))
        elif time_period == 'month':
            query = query.filter(created_at__gte=now - timedelta(days=30))
        elif time_period == 'year':
            query = query.filter(created_at__gte=now - timedelta(days=365))
    
    total_messages = query.count()
    
    return JsonResponse({
        'total_messages': total_messages
    })


def get_unique_users(request):
    """API endpoint to get the number of unique users"""
    time_period = request.GET.get('period', 'all')
    
    # Base query
    query = Conversation.objects.all()
    
    # Filter by time period
    if time_period != 'all':
        now = timezone.now()
        if time_period == 'today':
            query = query.filter(created_at__date=now.date())
        elif time_period == 'week':
            query = query.filter(created_at__gte=now - timedelta(days=7))
        elif time_period == 'month':
            query = query.filter(created_at__gte=now - timedelta(days=30))
        elif time_period == 'year':
            query = query.filter(created_at__gte=now - timedelta(days=365))
    
    unique_users = query.values('from_number').distinct().count()
    
    return JsonResponse({
        'unique_users': unique_users
    })


def get_active_chatbots(request):
    """API endpoint to get the number of active chatbots"""
    time_period = request.GET.get('period', 'all')
    
    # Base query - active chatbots
    query = Chatbot.objects.filter(is_active=True)
    
    # For time periods, we'll consider chatbots that have had conversations in that period
    if time_period != 'all':
        now = timezone.now()
        if time_period == 'today':
            date_filter = {'conversations__created_at__date': now.date()}
        elif time_period == 'week':
            date_filter = {'conversations__created_at__gte': now - timedelta(days=7)}
        elif time_period == 'month':
            date_filter = {'conversations__created_at__gte': now - timedelta(days=30)}
        elif time_period == 'year':
            date_filter = {'conversations__created_at__gte': now - timedelta(days=365)}
            
        query = query.filter(**date_filter).distinct()
    
    active_chatbots = query.count()
    
    return JsonResponse({
        'active_chatbots': active_chatbots
    })


def get_avg_response_time(request):
    """API endpoint to get the average response time"""
    time_period = request.GET.get('period', 'all')
    
    # This is a placeholder calculation - adjust based on your actual model structure
    # In a real implementation, you would calculate the time between user messages and bot responses
    
    # Simulated average response time calculation
    # In a real application, you would use a query like:
    # avg_time = Message.objects.filter(is_from_bot=True).annotate(
    #     response_time=ExpressionWrapper(F('timestamp') - F('previous_message_timestamp'), 
    #                                    output_field=FloatField())
    # ).aggregate(avg=Avg('response_time'))['avg']
    
    # For this example, we'll return simulated data
    if time_period == 'today':
        avg_time = 1.8
    elif time_period == 'week':
        avg_time = 2.1
    elif time_period == 'month':
        avg_time = 2.4
    elif time_period == 'year':
        avg_time = 2.7
    else:  # all time
        avg_time = 1
    
    return JsonResponse({
        'avg_response_time': avg_time
    })


def get_message_volume_data(request):
    """API endpoint to get message volume data for the chart"""
    time_period = request.GET.get('period', 'week')
    
    # Determine the appropriate time truncation and time range
    now = timezone.now()
    
    if time_period == 'today':
        # For today, get hourly data
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        labels = [f"{hour}:00" for hour in range(24)]
        
        # Initialize data array with zeros
        data = [0] * 24
        
        # Get actual message counts by hour
        from django.db.models.functions import ExtractHour
        hourly_counts = Message.objects.filter(created_at__date=now.date())\
            .annotate(hour=ExtractHour('created_at'))\
            .values('hour')\
            .annotate(count=Count('message_id'))\
            .order_by('hour')
        
        # Populate data array with actual counts
        for entry in hourly_counts:
            hour = entry['hour']
            if 0 <= hour < 24:  # Ensure hour is valid
                data[hour] = entry['count']
        
    elif time_period == 'week':
        # For week, get daily data
        start_date = now - timedelta(days=6)
        labels = [(now - timedelta(days=i)).strftime('%a') for i in range(6, -1, -1)]
        
        # Initialize data array with zeros
        data = [0] * 7
        
        # Get actual message counts by day
        daily_counts = Message.objects.filter(created_at__gte=start_date)\
            .annotate(day=TruncDay('created_at'))\
            .values('day')\
            .annotate(count=Count('message_id'))\
            .order_by('day')
        
        # Populate data array with actual counts
        for i, day_date in enumerate([(now - timedelta(days=i)).date() for i in range(6, -1, -1)]):
            for entry in daily_counts:
                if entry['day'].date() == day_date:
                    data[i] = entry['count']
                    break
        
    elif time_period == 'month':
        # For month, get weekly data
        start_date = now - timedelta(days=30)
        
        # Create week labels and start dates
        week_starts = []
        for i in range(4):
            week_start = now - timedelta(days=7*i + 6)
            week_starts.append(week_start)
        
        labels = [f"Week {i+1}" for i in range(4)]
        
        # Initialize data array with zeros
        data = [0] * 4
        
        # Get actual message counts by week
        for i, week_start in enumerate(week_starts):
            week_end = week_start + timedelta(days=6)
            count = Message.objects.filter(
                created_at__gte=week_start,
                created_at__lte=week_end
            ).count()
            data[i] = count
        
    elif time_period == 'year':
        # For year, get monthly data
        start_date = now - timedelta(days=365)
        labels = [(now - timedelta(days=30*i)).strftime('%b') for i in range(11, -1, -1)]
        
        # Initialize data array with zeros
        data = [0] * 12
        
        # Get actual message counts by month
        monthly_counts = Message.objects.filter(created_at__gte=start_date)\
            .annotate(month=TruncMonth('created_at'))\
            .values('month')\
            .annotate(count=Count('message_id'))\
            .order_by('month')
        
        # Populate data array with actual counts
        for i, month_date in enumerate([(now - timedelta(days=30*i)) for i in range(11, -1, -1)]):
            for entry in monthly_counts:
                if entry['month'].month == month_date.month and entry['month'].year == month_date.year:
                    data[i] = entry['count']
                    break
    
    else:  # Default to week
        start_date = now - timedelta(days=6)
        labels = [(now - timedelta(days=i)).strftime('%a') for i in range(6, -1, -1)]
        
        # Initialize data array with zeros
        data = [0] * 7
        
        # Get actual message counts by day
        daily_counts = Message.objects.filter(created_at__gte=start_date)\
            .annotate(day=TruncDay('created_at'))\
            .values('day')\
            .annotate(count=Count('message_id'))\
            .order_by('day')
        
        # Populate data array with actual counts
        for i, day_date in enumerate([(now - timedelta(days=i)).date() for i in range(6, -1, -1)]):
            for entry in daily_counts:
                if entry['day'].date() == day_date:
                    data[i] = entry['count']
                    break
    
    return JsonResponse({
        'labels': labels,
        'data': data
    })


def get_user_engagement_data(request):
    """API endpoint to get user engagement data for the chart"""
    time_period = request.GET.get('period', 'week')
    
    # Determine the appropriate time truncation and time range
    now = timezone.now()
    
    if time_period == 'today':
        # For today, get hourly data
        labels = [f"{hour}:00" for hour in range(24)]
        
        # Initialize data arrays with zeros
        active_users = [0] * 24
        new_users = [0] * 24
        
        # Get actual active users by hour (users who had conversations)
        from django.db.models.functions import ExtractHour
        hourly_active = Conversation.objects.filter(created_at__date=now.date())\
            .annotate(hour=ExtractHour('created_at'))\
            .values('hour')\
            .annotate(count=Count('from_number', distinct=True))\
            .order_by('hour')
        
        # Get actual new users by hour (first-time users)
        # This assumes you have a way to identify new users, adjust as needed
        hourly_new = Conversation.objects.filter(
                created_at__date=now.date(),
                # Add condition to identify new users
                # For example: is_first_conversation=True
            )\
            .annotate(hour=ExtractHour('created_at'))\
            .values('hour')\
            .annotate(count=Count('from_number', distinct=True))\
            .order_by('hour')
        
        # Populate data arrays with actual counts
        for entry in hourly_active:
            hour = entry['hour']
            if 0 <= hour < 24:  # Ensure hour is valid
                active_users[hour] = entry['count']
        
        for entry in hourly_new:
            hour = entry['hour']
            if 0 <= hour < 24:  # Ensure hour is valid
                new_users[hour] = entry['count']
        
    elif time_period == 'week':
        # For week, get daily data
        start_date = now - timedelta(days=6)
        labels = [(now - timedelta(days=i)).strftime('%a') for i in range(6, -1, -1)]
        
        # Initialize data arrays with zeros
        active_users = [0] * 7
        new_users = [0] * 7
        
        # Get actual active users by day
        daily_active = Conversation.objects.filter(created_at__gte=start_date)\
            .annotate(day=TruncDay('created_at'))\
            .values('day')\
            .annotate(count=Count('from_number', distinct=True))\
            .order_by('day')
        
        # Get actual new users by day
        # This assumes you have a way to identify new users, adjust as needed
        daily_new = Conversation.objects.filter(
                created_at__gte=start_date,
                # Add condition to identify new users
                # For example: is_first_conversation=True
            )\
            .annotate(day=TruncDay('created_at'))\
            .values('day')\
            .annotate(count=Count('from_number', distinct=True))\
            .order_by('day')
        
        # Populate data arrays with actual counts
        for i, day_date in enumerate([(now - timedelta(days=i)).date() for i in range(6, -1, -1)]):
            for entry in daily_active:
                if entry['day'].date() == day_date:
                    active_users[i] = entry['count']
                    break
            
            for entry in daily_new:
                if entry['day'].date() == day_date:
                    new_users[i] = entry['count']
                    break
        
    elif time_period == 'month':
        # For month, get weekly data
        start_date = now - timedelta(days=30)
        
        # Create week labels and start dates
        week_starts = []
        for i in range(4):
            week_start = now - timedelta(days=7*i + 6)
            week_starts.append(week_start)
        
        labels = [f"Week {i+1}" for i in range(4)]
        
        # Initialize data arrays with zeros
        active_users = [0] * 4
        new_users = [0] * 4
        
        # Get actual active and new users by week
        for i, week_start in enumerate(week_starts):
            week_end = week_start + timedelta(days=6)
            
            # Active users for this week
            active_count = Conversation.objects.filter(
                created_at__gte=week_start,
                created_at__lte=week_end
            ).values('from_number').distinct().count()
            
            # New users for this week (adjust as needed)
            new_count = Conversation.objects.filter(
                created_at__gte=week_start,
                created_at__lte=week_end,
                # Add condition to identify new users
                # For example: is_first_conversation=True
            ).values('from_number').distinct().count()
            
            active_users[i] = active_count
            new_users[i] = new_count
        
    elif time_period == 'year':
        # For year, get monthly data
        start_date = now - timedelta(days=365)
        labels = [(now - timedelta(days=30*i)).strftime('%b') for i in range(11, -1, -1)]
        
        # Initialize data arrays with zeros
        active_users = [0] * 12
        new_users = [0] * 12
        
        # Get actual active users by month
        monthly_active = Conversation.objects.filter(created_at__gte=start_date)\
            .annotate(month=TruncMonth('created_at'))\
            .values('month')\
            .annotate(count=Count('from_number', distinct=True))\
            .order_by('month')
        
        # Get actual new users by month
        # This assumes you have a way to identify new users, adjust as needed
        monthly_new = Conversation.objects.filter(
                created_at__gte=start_date,
                # Add condition to identify new users
                # For example: is_first_conversation=True
            )\
            .annotate(month=TruncMonth('created_at'))\
            .values('month')\
            .annotate(count=Count('from_number', distinct=True))\
            .order_by('month')
        
        # Populate data arrays with actual counts
        for i, month_date in enumerate([(now - timedelta(days=30*i)) for i in range(11, -1, -1)]):
            for entry in monthly_active:
                if entry['month'].month == month_date.month and entry['month'].year == month_date.year:
                    active_users[i] = entry['count']
                    break
            
            for entry in monthly_new:
                if entry['month'].month == month_date.month and entry['month'].year == month_date.year:
                    new_users[i] = entry['count']
                    break
    
    else:  # Default to week
        start_date = now - timedelta(days=6)
        labels = [(now - timedelta(days=i)).strftime('%a') for i in range(6, -1, -1)]
        
        # Initialize data arrays with zeros
        active_users = [0] * 7
        new_users = [0] * 7
        
        # Get actual active users by day
        daily_active = Conversation.objects.filter(created_at__gte=start_date)\
            .annotate(day=TruncDay('created_at'))\
            .values('day')\
            .annotate(count=Count('from_number', distinct=True))\
            .order_by('day')
        
        # Get actual new users by day
        # This assumes you have a way to identify new users, adjust as needed
        daily_new = Conversation.objects.filter(
                created_at__gte=start_date,
                # Add condition to identify new users
                # For example: is_first_conversation=True
            )\
            .annotate(day=TruncDay('created_at'))\
            .values('day')\
            .annotate(count=Count('from_number', distinct=True))\
            .order_by('day')
        
        # Populate data arrays with actual counts
        for i, day_date in enumerate([(now - timedelta(days=i)).date() for i in range(6, -1, -1)]):
            for entry in daily_active:
                if entry['day'].date() == day_date:
                    active_users[i] = entry['count']
                    break
            
            for entry in daily_new:
                if entry['day'].date() == day_date:
                    new_users[i] = entry['count']
                    break
    
    return JsonResponse({
        'labels': labels,
        'active_users': active_users,
        'new_users': new_users
    })


def get_channel_distribution_data(request):
    """API endpoint to get channel distribution data for the chart"""
    time_period = request.GET.get('period', 'all')
    
    # Get all available channels from the database
    all_channels = Channel.objects.all()
    channels = [channel.channel_type for channel in all_channels]
    
    # If no channels exist yet, provide some defaults
    if not channels:
        channels = ['Web', 'WhatsApp', 'Messenger', 'Email']
    
    # Prepare filter based on time period
    if time_period == 'today':
        time_filter = {'created_at__date': timezone.now().date()}
    elif time_period == 'week':
        time_filter = {'created_at__gte': timezone.now() - timedelta(days=7)}
    elif time_period == 'month':
        time_filter = {'created_at__gte': timezone.now() - timedelta(days=30)}
    elif time_period == 'year':
        time_filter = {'created_at__gte': timezone.now() - timedelta(days=365)}
    else:  # all time
        time_filter = {}
    
    # Get message counts by channel
    message_counts = []
    user_counts = []
    avg_response_times = []
    channel_breakdown = []
    
    for channel in all_channels:
        # Message count for this channel
        message_count = 0
        
        # Unique user count for this channel
        user_count = Conversation.objects.filter(
            channel=channel,
            **time_filter
        ).values('from_number').distinct().count()
        user_counts.append(user_count)
        
        # Average response time for this channel
        # This is a placeholder calculation - adjust based on your actual model structure
        # In a real implementation, you would calculate the time between user messages and bot responses
        # For now, we'll use a default value
        avg_response_time = 2.0
        
        
        avg_response_times.append(avg_response_time)
        
        # Add to channel breakdown
        channel_breakdown.append({
            'channel': channel.channel_type,
            'messages': message_count,
            'users': user_count,
            'avg_response': f"{avg_response_time}s"
        })
    
    # If we're using default channels (no channels in database),
    # create some empty data
    if not all_channels:
        message_counts = [0] * len(channels)
        user_counts = [0] * len(channels)
        avg_response_times = [0.0] * len(channels)
        
        channel_breakdown = []
        for i, channel in enumerate(channels):
            channel_breakdown.append({
                'channel': channel,
                'messages': 0,
                'users': 0,
                'avg_response': "0.0s"
            })
    
    return JsonResponse({
        'channels': channels,
        'message_counts': message_counts,
        'channel_breakdown': channel_breakdown
    })


def get_chatbot_performance_data(request):
    """API endpoint to get performance data for all chatbots"""
    time_period = request.GET.get('period', 'all')
    
    # Prepare filter based on time period
    if time_period == 'today':
        time_filter = {'created_at__date': timezone.now().date()}
    elif time_period == 'week':
        time_filter = {'created_at__gte': timezone.now() - timedelta(days=7)}
    elif time_period == 'month':
        time_filter = {'created_at__gte': timezone.now() - timedelta(days=30)}
    elif time_period == 'year':
        time_filter = {'created_at__gte': timezone.now() - timedelta(days=365)}
    else:  # all time
        time_filter = {}
    
    # Get all active chatbots
    active_chatbots = Chatbot.objects.filter(is_active=True, user=request.user)
    
    chatbots_data = []
    
    for chatbot in active_chatbots:
        # Get message count for this chatbot
        
        
        # Get unique user count for this chatbot
        user_count = Conversation.objects.filter(
            chatbot=chatbot,
            **time_filter
        ).values('from_number', 'from_email').distinct().count()
        
        message_count = chatbot.get_messages_count()
        
        satisfaction_rate = 85
        
        
        
        chatbots_data.append({
            'id': chatbot.chatbot_id,
            'name': chatbot.name,
            'message_count': message_count,
            'user_count': user_count,
            'satisfaction_rate': satisfaction_rate
        })
    
    return JsonResponse({
        'chatbots': chatbots_data
    })


def get_recent_activity_data(request):
    """API endpoint to get recent activity data"""
    # Get recent conversations (last 24 hours)
    recent_conversations = Conversation.objects.filter(
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).order_by('-created_at')[:10]  # Limit to 10 most recent
    
    # Get recent knowledge base updates (last 24 hours)
    recent_kb_updates = DataSource.objects.filter(
        updated_at__gte=timezone.now() - timedelta(hours=24)
    ).order_by('-updated_at')[:5]  # Limit to 5 most recent
    
    activities = []
    
    # Add recent conversations to activities
    for conversation in recent_conversations:
        try:
            chatbot_name = conversation.chatbot.name if conversation.chatbot else "Unknown Bot"
            
            # Format time difference
            time_diff = timezone.now() - conversation.created_at
            if time_diff.days > 0:
                time_str = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
            elif time_diff.seconds >= 3600:
                hours = time_diff.seconds // 3600
                time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif time_diff.seconds >= 60:
                minutes = time_diff.seconds // 60
                time_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                time_str = "just now"
            
            activities.append({
                'type': 'new_conversation',
                'icon': 'user',
                'icon_bg': 'primary',
                'message': f'New conversation started with <strong>{chatbot_name}</strong>',
                'time': time_str
            })
        except Exception as e:
            # Skip this conversation if there was an error
            continue
    
    # Add recent knowledge base updates to activities
    for datasource in recent_kb_updates:
        try:
            kb_name = datasource.knowledge_base.name if datasource.knowledge_base else "Unknown KB"
            
            # Format time difference
            time_diff = timezone.now() - datasource.updated_at
            if time_diff.days > 0:
                time_str = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
            elif time_diff.seconds >= 3600:
                hours = time_diff.seconds // 3600
                time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif time_diff.seconds >= 60:
                minutes = time_diff.seconds // 60
                time_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                time_str = "just now"
            
            activities.append({
                'type': 'knowledge_base',
                'icon': 'book',
                'icon_bg': 'info',
                'message': f'Knowledge base <strong>{kb_name}</strong> updated with new content',
                'time': time_str
            })
        except Exception as e:
            # Skip this datasource if there was an error
            continue
    
    # If no activities were found, provide a default message
    if not activities:
        activities.append({
            'type': 'info',
            'icon': 'info-circle',
            'icon_bg': 'secondary',
            'message': 'No recent activity in the last 24 hours',
            'time': 'now'
        })
    
    # Sort activities by time (most recent first)
    # This is a simple approach - in a real implementation, you might want to
    # parse the time strings and sort based on actual timestamps
    activities = sorted(activities, key=lambda x: x['time'], reverse=True)
    
    return JsonResponse({
        'activities': activities
    })